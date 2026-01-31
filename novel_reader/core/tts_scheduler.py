"""
TTSScheduler - TTS合成调度器

职责：
1. 管理TTS任务队列（优先级）
2. 调度Piper合成
3. 管理音频缓存
4. 预合成策略
"""
import os
import subprocess
import threading
import queue
import time
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import wave

from .models import TextChunk, Chapter, Book, TTSConfig, ChunkStatus, AUDIOBOOK_CONFIG
from .audio_cache import AudioCache
from .chunk_manager import ChunkManager


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
    chunk_id: int = field(compare=False)
    text: str = field(compare=False)
    book_id: int = field(compare=False)
    audio_path: str = field(compare=False)


class TTSScheduler:
    """
    TTS调度器 - 核心合成策略

    特性：
    - 优先级队列（当前chunk最高优先级）
    - 预合成机制
    - 音频缓存
    - 可中断/恢复
    """

    def __init__(self, config: dict = None):
        """
        初始化TTS调度器

        Args:
            config: 配置字典
        """
        self.config = config or AUDIOBOOK_CONFIG
        self.chunk_manager = ChunkManager(self.config)
        self.audio_cache = AudioCache(self.config.get("audio_cache_size", 80))

        # TTS配置
        self.tts_config = TTSConfig()

        # 任务队列
        self.queue = queue.PriorityQueue(
            maxsize=self.config.get("max_tts_queue", 5)
        )

        # 工作线程
        self.worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False

        # 当前状态
        self.current_chunk_id: Optional[int] = None
        self.current_book_id: Optional[int] = None

    def start(self):
        """启动TTS工作线程"""
        if self._running:
            return

        self._running = True
        self._paused = False
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True
        )
        self.worker_thread.start()
        print("[TTSScheduler] Started")

    def stop(self):
        """停止TTS工作线程"""
        self._running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[TTSScheduler] Stopped")

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
        audio_path = self.chunk_manager.get_audio_path(book_id, chunk.chunk_id)

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
        except queue.Full:
            print(f"[TTSScheduler] Queue full, dropping task: chunk {chunk.chunk_id}")

    def schedule_chapter(self, chapter: Chapter, book_id: int,
                          start_chunk_id: int = None):
        """
        调度整章chunks

        Args:
            chapter: 章节
            book_id: 书籍ID
            start_chunk_id: 起始chunk ID（用于预合成）
        """
        if start_chunk_id is None:
            start_chunk_id = chapter.chunks[0].chunk_id

        # 预合成数量
        prefetch = self.config.get("prefetch_chunks", 2)
        batch_size = self.config.get("tts_batch_chunks", 3)

        chunks_to_schedule = []
        for chunk in chapter.chunks:
            if chunk.chunk_id < start_chunk_id:
                continue

            chunks_to_schedule.append(chunk)

            # 限制调度数量
            if len(chunks_to_schedule) >= batch_size:
                break

        # 按优先级添加到队列
        for i, chunk in enumerate(chunks_to_schedule):
            if chunk.status == ChunkStatus.DONE:
                continue

            # 计算优先级
            if chunk.chunk_id == start_chunk_id:
                priority = TaskPriority.URGENT
            elif i < prefetch:
                priority = TaskPriority.HIGH
            else:
                priority = TaskPriority.NORMAL

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
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TTSScheduler] Error processing task: {e}")

    def _process_task(self, task: TTSTask):
        """
        处理TTS任务

        Args:
            task: TTS任务
        """
        # 检查缓存
        cache_key = self.chunk_manager.calculate_hash(
            task.text,
            self.tts_config.model_path,
            self.tts_config.voice
        )

        # 如果缓存中有，直接使用
        if self.audio_cache.contains(cache_key):
            cached = self.audio_cache.get(cache_key)
            if cached and Path(cached[0]).exists():
                print(f"[TTSScheduler] Cache HIT: chunk {task.chunk_id}")
                return

        # 检查文件是否已存在
        if Path(task.audio_path).exists():
            # 检查文件大小
            file_size = Path(task.audio_path).stat().st_size
            if file_size > 20000:  # 大于20KB认为有效
                # 计算时长并添加到缓存
                duration = self._get_audio_duration(task.audio_path)
                self.audio_cache.put(cache_key, task.audio_path, duration)
                return

        # 执行TTS合成
        print(f"[TTSScheduler] Synthesizing chunk {task.chunk_id} (priority={task.priority.name})")
        success = self._synthesize(task)

        if success:
            # 计算时长并添加到缓存
            duration = self._get_audio_duration(task.audio_path)
            self.audio_cache.put(cache_key, task.audio_path, duration)
            print(f"[TTSScheduler] ✓ Chunk {task.chunk_id} ({duration/1000:.1f}s)")

    def _synthesize(self, task: TTSTask) -> bool:
        """
        执行TTS合成

        Args:
            task: TTS任务

        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            Path(task.audio_path).parent.mkdir(parents=True, exist_ok=True)

            # 构建命令
            cmd = [
                self.tts_config.piper_bin,
                "--model", self.tts_config.model_path,
                "--config", self.tts_config.config_path,
                "-f", task.audio_path
            ]

            # 调用Piper
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(
                input=task.text,
                timeout=300  # 5分钟超时
            )

            if process.returncode != 0:
                print(f"[TTSScheduler] Piper error: {stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            process.kill()
            print(f"[TTSScheduler] Timeout: chunk {task.chunk_id}")
            return False
        except Exception as e:
            print(f"[TTSScheduler] Error: {e}")
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
        except:
            return 0

    def is_ready(self, chunk: TextChunk, book_id: int) -> bool:
        """
        检查chunk是否准备好

        Args:
            chunk: chunk对象
            book_id: 书籍ID

        Returns:
            是否准备好
        """
        audio_path = self.chunk_manager.get_audio_path(book_id, chunk.chunk_id)
        return Path(audio_path).exists() and Path(audio_path).stat().st_size > 20000

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()

    def clear_queue(self):
        """清空队列"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break


# 全局单例
_tts_scheduler: Optional[TTSScheduler] = None


def get_tts_scheduler() -> TTSScheduler:
    """获取全局TTS调度器单例"""
    global _tts_scheduler
    if _tts_scheduler is None:
        _tts_scheduler = TTSScheduler()
        _tts_scheduler.start()
    return _tts_scheduler
