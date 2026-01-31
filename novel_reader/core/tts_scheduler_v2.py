"""
TTSScheduler - TTS合成调度器

Production级实现：
- 优先级队列（URGENT > HIGH > NORMAL > LOW）
- 后台工作线程
- Piper CLI集成
- 音频缓存集成
- 可中断/恢复
- 预合成策略
"""
import os
import subprocess
import threading
import time
import wave
from pathlib import Path
from typing import Optional, List, Tuple
from queue import PriorityQueue, Empty
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import OrderedDict
import hashlib

from .models_v2 import TextChunk, ChunkStatus, PlayerConfig, TTSConfig
from .audio_cache import AudioCache


class TaskPriority(Enum):
    """任务优先级"""
    URGENT = 0      # 当前正在播放的chunk
    HIGH = 1        # 紧接着的chunk
    NORMAL = 2      # 预合成chunk
    LOW = 3         # 远期chunk


@dataclass(order=True)
class TTSTask:
    """TTS任务"""
    priority: TaskPriority
    distance: int  # 距离当前chunk的距离
    created_at: float = field(default_factory=time.time, compare=False)
    chunk_id: int = field(default=0, compare=False)
    text: str = field(default="", compare=False)
    book_id: int = field(default=0, compare=False)
    audio_path: str = field(default="", compare=False)


class TTSScheduler:
    """
    TTS调度器 - 核心合成策略

    特性：
    - 优先级队列
    - 后台工作线程
    - 可中断
    - 预合成
    - 缓存集成
    """

    def __init__(self, config: PlayerConfig = None,
                 tts_config: TTSConfig = None,
                 audio_cache: AudioCache = None):
        """
        初始化TTS调度器

        Args:
            config: 播放器配置
            tts_config: TTS配置
            audio_cache: 音频缓存
        """
        self.config = config or PlayerConfig()
        self.tts_config = tts_config or TTSConfig()
        self.audio_cache = audio_cache or AudioCache(self.config.audio_cache_size)

        # 任务队列
        self.queue = PriorityQueue(maxsize=self.config.max_tts_queue)

        # 工作线程
        self.worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False

        # 当前状态
        self.current_chunk_id: Optional[int] = None
        self.current_book_id: Optional[int] = None

        # 统计
        self.completed_count = 0
        self.failed_count = 0
        self.cache_hits = 0

    def start(self):
        """启动TTS工作线程"""
        if self._running:
            return

        self._running = True
        self._paused = False
        self.completed_count = 0
        self.failed_count = 0
        self.cache_hits = 0

        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="TTSScheduler-Worker"
        )
        self.worker_thread.start()
        print("[TTSScheduler] ✓ Started")

    def stop(self):
        """停止TTS工作线程"""
        self._running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[TTSScheduler] ✓ Stopped")

    def pause(self):
        """暂停调度"""
        self._paused = True

    def resume(self):
        """恢复调度"""
        self._paused = False

    def schedule_chunk(self, chunk: TextChunk, book_id: int,
                      priority: TaskPriority = TaskPriority.NORMAL):
        """
        调度一个chunk进行合成

        Args:
            chunk: 要合成的chunk
            book_id: 书籍ID
            priority: 任务优先级
        """
        # 计算距离
        distance = 0
        if self.current_chunk_id is not None:
            distance = abs(chunk.chunk_id - self.current_chunk_id)

        # 获取音频路径
        audio_path = self._get_audio_path(book_id, chunk.chunk_id)

        # 创建任务
        task = TTSTask(
            priority=priority,
            distance=distance,
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            book_id=book_id,
            audio_path=audio_path
        )

        try:
            self.queue.put(task, block=False)
            print(f"[TTSScheduler] 📤 Scheduled chunk {chunk.chunk_id} ({priority.name})")
        except:
            print(f"[TTSScheduler] ⚠ Queue full, dropping chunk {chunk.chunk_id}")

    def schedule_chapter(self, chapter: 'Chapter', book_id: int,
                          start_chunk_id: int = None):
        """
        调度整章chunks

        Args:
            chapter: 章节
            book_id: 书籍ID
            start_chunk_id: 起始chunk ID
        """
        if start_chunk_id is None:
            start_chunk_id = chapter.chunks[0].chunk_id

        # 调度数量
        batch_size = self.config.tts_batch_chunks

        chunks_to_schedule = []
        for chunk in chapter.chunks:
            if chunk.chunk_id < start_chunk_id:
                continue

            if chunk.status in [ChunkStatus.DONE, ChunkStatus.PLAYING]:
                continue

            chunks_to_schedule.append(chunk)

            # 限制调度数量
            if len(chunks_to_schedule) >= batch_size:
                break

        # 按优先级添加到队列
        for i, chunk in enumerate(chunks_to_schedule):
            if chunk.status == ChunkStatus.TTS:
                continue  # 已在合成中

            if i == 0:
                priority = TaskPriority.URGENT
            elif i < self.config.prefetch_chunks:
                priority = TaskPriority.HIGH
            else:
                priority = TaskPriority.NORMAL

            chunk.mark_tts_started()
            self.schedule_chunk(chunk, book_id, priority)

    def _worker_loop(self):
        """工作线程主循环"""
        print("[TTSScheduler] Worker loop started")

        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            try:
                # 获取任务（带超时）
                task = self.queue.get(timeout=0.5)
                self._process_task(task)

            except Empty:
                continue
            except Exception as e:
                print(f"[TTSScheduler] ✗ Error: {e}")
                import traceback
                traceback.print_exc()

        print("[TTSScheduler] Worker loop stopped")

    def _process_task(self, task: TTSTask):
        """
        处理TTS任务

        Args:
            task: TTS任务
        """
        # 检查缓存
        cache_key = self._calculate_cache_hash(task.text)

        if self.audio_cache.contains(cache_key):
            cached = self.audio_cache.get(cache_key)
            if cached and Path(cached[0]).exists():
                self.cache_hits += 1
                print(f"[TTSScheduler] 💾 Cache HIT: chunk {task.chunk_id}")
                return

        # 检查文件是否已存在
        if Path(task.audio_path).exists():
            file_size = Path(task.audio_path).stat().st_size
            if file_size > 20000:  # 大于20KB认为有效
                # 计算时长并添加到缓存
                duration = self._get_audio_duration(task.audio_path)
                self.audio_cache.put(cache_key, task.audio_path, duration)
                return

        # 执行TTS合成
        print(f"[TTSScheduler] 🔊 Synthesizing chunk {task.chunk_id} (priority={task.priority.name})")

        # 确保目录存在
        Path(task.audio_path).parent.mkdir(parents=True, exist_ok=True)

        success = self._synthesize(task)

        if success:
            self.completed_count += 1

            # 计算时长并添加到缓存
            duration = self._get_audio_duration(task.audio_path)
            self.audio_cache.put(cache_key, task.audio_path, duration)

            print(f"[TTSScheduler] ✓ Chunk {task.chunk_id} ({duration/1000:.1f}s, {len(task.text)} chars)")
        else:
            self.failed_count += 1

    def _synthesize(self, task: TTSTask) -> bool:
        """
        执行TTS合成

        Args:
            task: TTS任务

        Returns:
            是否成功
        """
        cmd = [
            self.tts_config.piper_bin,
            "--model", self.tts_config.model_path,
            "--config", self.tts_config.config_path,
            "-f", task.audio_path
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(
                input=task.text,
                timeout=self.config.tts_timeout
            )

            if process.returncode != 0:
                print(f"[TTSScheduler] ✗ Piper error (code={process.returncode}): {stderr[:200]}")
                return False

            return True

        except subprocess.TimeoutExpired:
            process.kill()
            print(f"[TTSScheduler] ⏱ Timeout: chunk {task.chunk_id}")
            # 删除可能损坏的文件
            if Path(task.audio_path).exists():
                Path(task.audio_path).unlink()
            return False

        except Exception as e:
            print(f"[TTSScheduler] ✗ Error: {e}")
            return False

    def _get_audio_duration(self, audio_path: str) -> int:
        """
        获取音频时长（毫秒）

        Args:
            audio_path: 音频文件路径

        Returns:
            时长（毫秒）
        """
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / rate
                return int(duration * 1000)
        except Exception as e:
            print(f"[TTSScheduler] ⚠ Could not get duration: {e}")
            return 0

    def _get_audio_path(self, book_id: int, chunk_id: int) -> str:
        """获取音频文件路径"""
        audio_dir = Path("data/audio") / str(book_id)
        return str(audio_dir / f"chunk_{chunk_id:05d}.wav")

    def _calculate_cache_hash(self, text: str) -> str:
        """计算缓存hash"""
        content = f"{text}|{self.tts_config.model_path}|{self.tts_config.voice}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def is_ready(self, chunk: TextChunk, book_id: int) -> bool:
        """
        检查chunk是否准备好

        Args:
            chunk: chunk对象
            book_id: 书籍ID

        Returns:
            是否准备好
        """
        audio_path = self._get_audio_path(book_id, chunk.chunk_id)
        if not Path(audio_path).exists():
            return False

        return Path(audio_path).stat().st_size > 20000

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()

    def clear_queue(self):
        """清空队列"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break

    @property
    def stats(self) -> dict:
        """获取统计信息"""
        return {
            "completed": self.completed_count,
            "failed": self.failed_count,
            "cache_hits": self.cache_hits,
            "queue_size": self.get_queue_size()
        }

    def __repr__(self) -> str:
        return f"TTSScheduler(running={self._running}, stats={self.stats})"
