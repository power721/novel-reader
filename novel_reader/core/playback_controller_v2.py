"""
PlaybackController - 播放控制器（核心大脑）

Production级实现：
- 完整的状态机（STOPPED/PLAYING/PAUSED/SEEKING）
- 调度 TTS 和 AudioPlayer
- 章节管理
- seek 支持（精确到毫秒）
- 线程安全
"""
import time
import threading
from queue import Queue, Empty
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum, auto

from .models_v2 import (
    Book, Chapter, TextChunk, PlaybackState, ChunkStatus,
    PlayerConfig, TTSConfig
)
from .chunk_manager_v2 import ChunkManager
from .audio_player_v2 import AudioPlayer, MpvAudioPlayer
from .audio_cache import AudioCache
from .tts_scheduler_v2 import TTSScheduler, TTSTask, TaskPriority
from .settings import get_setting


class PlayerEvent(Enum):
    """播放器事件"""
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()
    SEEK = auto()
    NEXT_CHAPTER = auto()
    PREV_CHAPTER = auto()
    CHUNK_FINISHED = auto()
    CHAPTER_FINISHED = auto()
    SHUTDOWN = auto()


@dataclass
class Event:
    """事件数据"""
    type: PlayerEvent
    data: Optional[any] = None


class PlaybackController:
    """
    播放控制器 - 核心状态机

    这是整个播放器的大脑，负责：
    - 播放状态管理
    - 调度 TTS 合成
    - 控制 AudioPlayer
    - 处理用户操作
    - 管理章节切换

    线程模型：
    - 主线程：控制逻辑
    - TTS Worker Thread：合成
    - Audio Player Thread：播放
    - 事件队列：线程间通信
    """

    def __init__(self, config: PlayerConfig = None, tts_config: TTSConfig = None):
        """
        初始化播放控制器

        Args:
            config: 播放器配置
            tts_config: TTS配置
        """
        self.config = config or PlayerConfig()
        self.tts_config = tts_config or TTSConfig()

        # 核心组件
        self.chunk_manager = ChunkManager(self.config)
        self.audio_cache = AudioCache(self.config.audio_cache_size)
        self.audio_player = self._create_audio_player()

        # 播放状态
        self.state = PlaybackState.STOPPED
        self.current_book: Optional[Book] = None
        self.current_chapter: Optional[Chapter] = None
        self.current_chunk: Optional[TextChunk] = None
        self.current_chunk_index: int = 0

        # 播放位置
        self.current_offset_ms: int = 0

        # TTS调度器
        self.tts_scheduler: Optional[TTSScheduler] = None

        # 事件队列（线程间通信）
        self.event_queue: Queue = Queue()
        self._running = False

        # 事件处理线程
        self.event_thread: Optional[threading.Thread] = None

        # 回调函数
        self.on_state_changed: Optional[Callable[[PlaybackState], None]] = None
        self.on_chunk_changed: Optional[Callable[[TextChunk], None]] = None
        self.on_chapter_changed: Optional[Callable[[Chapter], None]] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None  # (current_ms, total_ms)
        self.on_book_finished: Optional[Callable] = None

    def _create_audio_player(self):
        """创建音频播放器"""
        # 尝试使用 sounddevice
        try:
            return AudioPlayer()
        except RuntimeError:
            print("[PlaybackController] Using mpv player as fallback")
            return MpvAudioPlayer()

    def start(self):
        """启动播放控制器"""
        if self._running:
            return

        self._running = True

        # 启动TTS调度器
        self.tts_scheduler = TTSScheduler(
            config=self.config,
            tts_config=self.tts_config,
            audio_cache=self.audio_cache
        )
        self.tts_scheduler.start()

        # 启动事件处理线程
        self.event_thread = threading.Thread(
            target=self._event_loop,
            daemon=True,
            name="PlaybackController-EventLoop"
        )
        self.event_thread.start()

        print("[PlaybackController] ✓ Started")

    def stop(self):
        """停止播放控制器"""
        if not self._running:
            return

        self._running = False

        # 停止播放
        self.audio_player.stop()

        # 停止TTS调度器
        if self.tts_scheduler:
            self.tts_scheduler.stop()

        # 发送关闭事件
        self._post_event(PlayerEvent.SHUTDOWN)

        # 等待事件线程结束
        if self.event_thread:
            self.event_thread.join(timeout=2)

        print("[PlaybackController] ✓ Stopped")

    def load_book(self, book_id: int, file_path: str = "") -> Book:
        """
        加载书籍

        Args:
            book_id: 书籍ID
            file_path: 文件路径

        Returns:
            Book对象
        """
        # 停止当前播放
        if self.state == PlaybackState.PLAYING:
            self.stop()

        # 解析书籍
        book = self.chunk_manager.parse_book(file_path, book_id)

        # 确保音频目录存在
        for chapter in book.chapters:
            self.chunk_manager.ensure_audio_dir(book_id)

        self.current_book = book
        self.current_chunk_index = 0

        print(f"[PlaybackController] ✓ Loaded book: {book}")
        return book

    def play(self):
        """开始/恢复播放"""
        if not self.current_book:
            print("[PlaybackController] ✗ No book loaded")
            return

        self._post_event(PlayerEvent.PLAY)

    def pause(self):
        """暂停播放"""
        if self.state == PlaybackState.PLAYING:
            self._post_event(PlayerEvent.PAUSE)

    def resume(self):
        """恢复播放"""
        if self.state == PlaybackState.PAUSED:
            self._post_event(PlayerEvent.PLAY)

    def stop(self):
        """停止播放"""
        self._post_event(PlayerEvent.STOP)

    def seek(self, chapter_index: int = None, chunk_index: int = None, offset_ms: int = 0):
        """
        Seek到指定位置

        Args:
            chapter_index: 章节索引
            chunk_index: chunk索引
            offset_ms: 偏移（毫秒）
        """
        self._post_event(PlayerEvent.SEEK, {
            "chapter_index": chapter_index,
            "chunk_index": chunk_index,
            "offset_ms": offset_ms
        })

    def next_chapter(self):
        """跳转到下一章"""
        self._post_event(PlayerEvent.NEXT_CHAPTER)

    def prev_chapter(self):
        """跳转到上一章"""
        self._post_event(PlayerEvent.PREV_CHAPTER)

    def _post_event(self, event_type: PlayerEvent, data: any = None):
        """
        发送事件到队列

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        try:
            self.event_queue.put(Event(event_type, data), block=False)
        except:
            print(f"[PlaybackController] ✗ Event queue full, dropping: {event_type}")

    def _event_loop(self):
        """事件处理循环（在单独线程中运行）"""
        print("[PlaybackController] Event loop started")

        while self._running:
            try:
                # 获取事件（带超时）
                event = self.event_queue.get(timeout=0.5)
                self._handle_event(event)
            except Empty:
                continue
            except Exception as e:
                print(f"[PlaybackController] ✗ Event handling error: {e}")

        print("[PlaybackController] Event loop stopped")

    def _handle_event(self, event: Event):
        """
        处理事件

        Args:
            event: 事件对象
        """
        if event.type == PlayerEvent.SHUTDOWN:
            # 关闭
            self.state = PlaybackState.STOPPED
            self._notify_state_changed()

        elif event.type == PlayerEvent.PLAY:
            self._handle_play()

        elif event.type == PlayerEvent.PAUSE:
            self._handle_pause()

        elif event.type == PlayerEvent.STOP:
            self._handle_stop()

        elif event.type == PlayerEvent.SEEK:
            self._handle_seek(event.data)

        elif event.type == PlayerEvent.NEXT_CHAPTER:
            self._handle_next_chapter()

        elif event.type == PlayerEvent.PREV_CHAPTER:
            self._handle_prev_chapter()

    def _handle_play(self):
        """处理播放事件"""
        if not self.current_book:
            return

        # 如果是暂停状态，恢复
        if self.state == PlaybackState.PAUSED:
            self.audio_player.resume()
            self.state = PlaybackState.PLAYING
            self._notify_state_changed()
            return

        # 获取当前chunk
        chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if not chunk:
            print(f"[PlaybackController] ✗ Chunk {self.current_chunk_index} not found")
            return

        self.current_chunk = chunk
        self.current_chapter = self.current_book.find_chapter_by_chunk_id(chunk.chunk_id)

        # 检查音频是否准备好
        audio_path = self.chunk_manager.get_audio_path(
            self.current_book.book_id,
            chunk.chunk_id
        )

        if not Path(audio_path).exists() or Path(audio_path).stat().st_size < 20000:
            print(f"[PlaybackController] ⏳ Audio not ready for chunk {chunk.chunk_id}, scheduling TTS...")
            # 调度TTS
            self._schedule_urgent_chunks(chunk)
            # 等待TTS完成（简化版：直接暂停）
            self.state = PlaybackState.PAUSED
            return

        # 开始播放
        self.state = PlaybackState.PLAYING
        self._notify_state_changed()

        # 播放音频
        self.audio_player.play(
            audio_path,
            start_offset_ms=0,
            on_finished=self._on_chunk_finished,
            on_progress=self._on_playback_progress
        )

        # 标记状态
        chunk.mark_playing()
        self._notify_chunk_changed()

        # 调度后续chunks
        self._schedule_next_chunks()

        print(f"[PlaybackController] ▶ Playing chunk {chunk.chunk_id}")

    def _handle_pause(self):
        """处理暂停事件"""
        if self.state == PlaybackState.PLAYING:
            self.audio_player.pause()
            self.state = PlaybackState.PAUSED
            self._notify_state_changed()
            print("[PlaybackController] ⏸ Paused")

    def _handle_stop(self):
        """处理停止事件"""
        self.audio_player.stop()
        self.state = PlaybackState.STOPPED
        self._notify_state_changed()
        print("[PlaybackController] ⏹ Stopped")

    def _handle_seek(self, data: dict):
        """处理seek事件"""
        chapter_index = data.get("chapter_index")
        chunk_index = data.get("chunk_index")
        offset_ms = data.get("offset_ms", 0)

        if not self.current_book:
            return

        self.state = PlaybackState.SEEKING
        self._notify_state_changed()

        # 停止当前播放
        was_playing = self.audio_player.is_playing
        self.audio_player.stop()

        # 定位chunk
        if chunk_index is not None:
            self.current_chunk_index = chunk_index
        elif chapter_index is not None:
            chapter = self.current_book.get_chapter_by_index(chapter_index)
            if chapter:
                self.current_chunk_index = chapter.start_index

        # 更新当前chunk和章节
        chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if chunk:
            self.current_chunk = chunk
            self._notify_chunk_changed()

        chapter = self.current_book.find_chapter_by_chunk_id(chunk.chunk_id)
        if chapter:
            self.current_chapter = chapter
            self._notify_chapter_changed()

        # 检查音频是否准备好
        audio_path = self.chunk_manager.get_audio_path(
            self.current_book.book_id,
            chunk.chunk_id
        )

        if Path(audio_path).exists() and Path(audio_path).stat().st_size > 20000:
            # 音频已准备好，立即播放
            if was_playing or self.state == PlaybackState.SEEKING:
                self.audio_player.play(
                    audio_path,
                    start_offset_ms=offset_ms,
                    on_finished=self._on_chunk_finished,
                    on_progress=self._on_playback_progress
                )
                chunk.mark_playing()
                self.state = PlaybackState.PLAYING
        else:
            # 音频未准备好，调度TTS
            print(f"[PlaybackController] ⏳ Seeking to unready chunk {chunk.chunk_id}")
            self._schedule_urgent_chunks(chunk)
            self.state = PlaybackState.PAUSED

        self._notify_state_changed()

    def _handle_next_chapter(self):
        """处理下一章事件"""
        if not self.current_book or not self.current_chapter:
            return

        current_ch_idx = self.current_book.chapters.index(self.current_chapter)
        if current_ch_idx + 1 < len(self.current_book.chapters):
            next_chapter = self.current_book.chapters[current_ch_idx + 1]
            self._handle_seek({"chunk_index": next_chapter.start_index})
            print(f"[PlaybackController] ⏭ Next chapter: {next_chapter.title}")

    def _handle_prev_chapter(self):
        """处理上一章事件"""
        if not self.current_book or not self.current_chapter:
            return

        current_ch_idx = self.current_book.chapters.index(self.current_chapter)
        if current_ch_idx > 0:
            prev_chapter = self.current_book.chapters[current_ch_idx - 1]
            self._handle_seek({"chunk_index": prev_chapter.start_index})
            print(f"[PlaybackController] ⏮ Prev chapter: {prev_chapter.title}")

    def _on_chunk_finished(self):
        """当前chunk播放完成回调"""
        if not self.current_chunk:
            return

        # 标记为完成
        self.current_chunk.mark_done()
        print(f"[PlaybackController] ✓ Chunk {self.current_chunk.chunk_id} finished")

        # 清理旧的音频文件
        self._cleanup_old_chunks()

        # 移动到下一个chunk
        self.current_chunk_index += 1

        # 检查是否到达书籍末尾
        if self.current_chunk_index >= self.current_book.total_chunks:
            print("[PlaybackController] 📚 Book finished!")
            self.state = PlaybackState.STOPPED
            self._notify_state_changed()
            if self.on_book_finished:
                self.on_book_finished()
            return

        # 获取下一个chunk
        next_chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if not next_chunk:
            self.state = PlaybackState.STOPPED
            return

        self.current_chunk = next_chunk

        # 检查是否切换章节
        next_chapter = self.current_book.find_chapter_by_chunk_id(next_chunk.chunk_id)
        if next_chapter != self.current_chapter:
            self.current_chapter = next_chapter
            self._notify_chapter_changed()

        self._notify_chunk_changed()

        # 检查音频是否准备好
        audio_path = self.chunk_manager.get_audio_path(
            self.current_book.book_id,
            next_chunk.chunk_id
        )

        if Path(audio_path).exists() and Path(audio_path).stat().st_size > 20000:
            # 音频已准备好，立即播放
            self.audio_player.play(
                audio_path,
                on_finished=self._on_chunk_finished,
                on_progress=self._on_playback_progress
            )
            next_chunk.mark_playing()
            self.state = PlaybackState.PLAYING
            print(f"[PlaybackController] ▶ Playing chunk {next_chunk.chunk_id}")

            # 调度后续chunks
            self._schedule_next_chunks()
        else:
            # 音频未准备好
            print(f"[PlaybackController] ⏳ Next chunk not ready, waiting...")
            self._schedule_urgent_chunks(next_chunk)
            self.state = PlaybackState.PAUSED

        self._notify_state_changed()

    def _on_playback_progress(self, current_ms: int, total_ms: int):
        """播放进度回调"""
        if self.on_progress:
            self.on_progress(current_ms, total_ms)

    def _schedule_urgent_chunks(self, chunk: TextChunk):
        """
        调度紧急chunks（当前chunk + 预取）

        Args:
            chunk: 当前chunk
        """
        if not self.tts_scheduler:
            return

        # 找到所属章节
        chapter = None
        for ch in self.current_book.chapters:
            if ch.start_index <= chunk.chunk_id < ch.end_index:
                chapter = ch
                break

        if chapter:
            # 调度当前章节（从当前chunk开始）
            self.tts_scheduler.schedule_chapter(
                chapter,
                self.current_book.book_id,
                start_chunk_id=chunk.chunk_id
            )

    def _schedule_next_chunks(self):
        """调度后续chunks（预合成）"""
        if not self.tts_scheduler or not self.current_chunk:
            return

        prefetch = self.config.prefetch_chunks

        for i in range(1, prefetch + 1):
            next_idx = self.current_chunk_index + i
            if next_idx < self.current_book.total_chunks:
                next_chunk = self.current_book.get_chunk_by_index(next_idx)
                if next_chunk and next_chunk.status == ChunkStatus.PENDING:
                    priority = TaskPriority.HIGH if i == 1 else TaskPriority.NORMAL
                    self.tts_scheduler.schedule_chunk(
                        next_chunk,
                        self.current_book.book_id,
                        priority
                    )

    def _cleanup_old_chunks(self):
        """清理旧的音频文件"""
        if not self.current_book:
            return

        threshold = get_setting("cleanup_old_chunk_threshold", 50)
        keep_chunk_index = max(0, self.current_chunk_index - threshold)

        print(f"[PlaybackController] 🔍 Cleanup: current={self.current_chunk_index}, threshold={threshold}, keep_after={keep_chunk_index}")

        if keep_chunk_index <= 0:
            print(f"[PlaybackController] ⏭️ Cleanup skipped: keep_chunk_index <= 0")
            return

        book_dir = self.chunk_manager.audio_dir / str(self.current_book.book_id)
        if not book_dir.exists():
            print(f"[PlaybackController] ⏭️ Cleanup skipped: audio dir not found")
            return

        deleted = 0
        checked = 0
        for audio_file in book_dir.glob("chunk_*.wav"):
            checked += 1
            try:
                chunk_id_str = audio_file.stem.split('_')
                if len(chunk_id_str) < 3:
                    continue

                # chunk_id 是最后一部分
                chunk_id = int(chunk_id_str[-1])
                if chunk_id < keep_chunk_index:
                    audio_file.unlink()
                    deleted += 1
                    print(f"[PlaybackController] 🗑 Deleted: {audio_file.name} (chunk {chunk_id})")
            except (ValueError, IndexError) as e:
                print(f"[PlaybackController] ⚠️ Parse error: {audio_file.name} - {e}")
                continue

        if deleted > 0:
            print(f"[PlaybackController] ✅ Cleaned up {deleted}/{checked} old audio files (before chunk {keep_chunk_index})")
        else:
            print(f"[PlaybackController] ℹ️ No files to delete (checked {checked} files)")

    def _notify_state_changed(self):
        """通知状态变化"""
        if self.on_state_changed:
            self.on_state_changed(self.state)

    def _notify_chunk_changed(self):
        """通知chunk变化"""
        if self.on_chunk_changed and self.current_chunk:
            self.on_chunk_changed(self.current_chunk)

    def _notify_chapter_changed(self):
        """通知章节变化"""
        if self.on_chapter_changed and self.current_chapter:
            self.on_chapter_changed(self.current_chapter)

    # 属性访问器
    @property
    def progress_percent(self) -> float:
        """播放进度百分比"""
        if not self.current_book:
            return 0.0
        return self.current_book.progress_percent

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlaybackState.PLAYING

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.state == PlaybackState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.state == PlaybackState.STOPPED


# 为了导入方便，导出AudioCache和TTSScheduler
from .audio_cache import AudioCache
