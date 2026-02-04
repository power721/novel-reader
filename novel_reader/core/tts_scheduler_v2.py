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

    def schedule_chunk_range(self, book_id: int, start_chunk_id: int,
                             num_chunks: int, chunks: List['TextChunk']):
        """
        调度指定范围的chunks（从start_chunk_id开始的num_chunks个）

        注意：此方法会立即返回，不阻塞调用者。
        批量文件检查在后台异步执行。

        Args:
            book_id: 书籍ID
            start_chunk_id: 起始chunk ID
            num_chunks: 要调度的chunk数量
            chunks: 所有可用的chunks列表
        """
        # 筛选指定范围的chunks
        target_chunks = []
        for chunk in chunks:
            if start_chunk_id <= chunk.chunk_id < start_chunk_id + num_chunks:
                # 跳过已完成或正在播放的chunks
                if chunk.status not in [ChunkStatus.DONE, ChunkStatus.PLAYING]:
                    target_chunks.append(chunk)

            if chunk.chunk_id >= start_chunk_id + num_chunks:
                break

        if not target_chunks:
            print(f"[TTSScheduler] No chunks to schedule in range [{start_chunk_id}, {start_chunk_id + num_chunks})")
            return

        # 异步批量检查音频文件（不阻塞）
        self._schedule_chunks_async(target_chunks, book_id, start_chunk_id)

    def schedule_chapter(self, chapter: 'Chapter', book_id: int,
                          start_chunk_id: int = None):
        """
        调度整章chunks

        注意：此方法会立即返回，不阻塞调用者。
        批量文件检查在后台异步执行。

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

        # 异步批量检查音频文件（不阻塞）
        self._schedule_chunks_async(chunks_to_schedule, book_id, start_chunk_id)

    def _schedule_chunks_async(self, chunks: List['TextChunk'], book_id: int,
                               base_chunk_id: int = None):
        """
        异步调度chunks（不阻塞）

        在后台线程中批量检查文件，然后添加需要转换的chunks到队列

        Args:
            chunks: chunk列表
            book_id: 书籍ID
            base_chunk_id: 基础chunk ID（用于计算优先级）
        """
        def _check_and_schedule():
            """后台线程：检查文件并调度"""
            # 批量检查音频文件，只调度需要转换的chunks
            chunks_to_convert = self._filter_chunks_need_conversion(
                chunks, book_id
            )

            # 按优先级添加到队列
            for i, chunk in enumerate(chunks_to_convert):
                if chunk.status == ChunkStatus.TTS:
                    continue  # 已在合成中

                # 根据距离计算优先级
                if base_chunk_id is not None:
                    distance = chunk.chunk_id - base_chunk_id
                else:
                    distance = 0

                if distance == 0:
                    priority = TaskPriority.URGENT
                elif distance < self.config.prefetch_chunks:
                    priority = TaskPriority.HIGH
                elif distance < self.config.prefetch_chunks * 2:
                    priority = TaskPriority.NORMAL
                else:
                    priority = TaskPriority.LOW

                chunk.mark_tts_started()
                self.schedule_chunk(chunk, book_id, priority)

        # 在后台线程中执行（不阻塞调用者）
        thread = threading.Thread(
            target=_check_and_schedule,
            daemon=True,
            name="TTSScheduler-CheckAndSchedule"
        )
        thread.start()

    def _filter_chunks_need_conversion(self, chunks: List['TextChunk'],
                                        book_id: int) -> List['TextChunk']:
        """
        批量检查chunks，过滤出需要转换的chunks

        检查每个chunk的音频文件是否已存在且有效，如果存在则跳过

        Args:
            chunks: chunk列表
            book_id: 书籍ID

        Returns:
            需要转换的chunk列表
        """
        chunks_need_conversion = []
        skipped_count = 0

        for chunk in chunks:
            audio_path = self._get_audio_path(book_id, chunk.chunk_id)
            audio_file = Path(audio_path)

            # 检查文件是否存在且有效
            if audio_file.exists():
                file_size = audio_file.stat().st_size
                if file_size > 20000:  # 大于20KB认为有效
                    # 音频文件已存在且有效，跳过
                    skipped_count += 1
                    # 更新chunk状态为READY
                    chunk.status = ChunkStatus.READY
                    continue
                else:
                    # 文件存在但太小（损坏），删除
                    try:
                        audio_file.unlink()
                        print(f"[TTSScheduler] 🗑 Deleted invalid audio file: chunk {chunk.chunk_id}")
                    except:
                        pass

            # 需要转换
            chunks_need_conversion.append(chunk)

        if skipped_count > 0:
            print(f"[TTSScheduler] ⏩ Skipped {skipped_count} chunks with existing audio")

        return chunks_need_conversion

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
        """获取音频文件路径（包含model_id）"""
        # 使用中文模型ID作为默认
        model_id = getattr(self.tts_config, 'chinese_model_id', 'xiao_ya')
        audio_dir = Path("data/audio") / str(book_id)
        return str(audio_dir / f"chunk_{model_id}_{chunk_id:05d}.wav")

    def _calculate_cache_hash(self, text: str) -> str:
        """计算缓存hash（包含model_id）"""
        model_id = getattr(self.tts_config, 'chinese_model_id', 'xiao_ya')
        content = f"{text}|{model_id}|{self.tts_config.voice}"
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
