"""
PlaybackController - 播放控制器（状态机）

这是播放器的大脑，负责：
1. 播放状态管理（状态机）
2. Chunk调度
3. TTS任务分配
4. AudioPlayer控制
5. seek/pause/resume
"""
import time
import threading
from enum import Enum, auto
from typing import Optional, List
from dataclasses import dataclass

from .models import Book, Chapter, TextChunk, PlaybackState, ChunkStatus, AUDIOBOOK_CONFIG
from .chunk_manager import ChunkManager
from .tts_scheduler import TTSScheduler, get_tts_scheduler, TaskPriority
from .audio_player import SimpleAudioPlayer


class PlayerEvent(Enum):
    """播放器事件"""
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()
    SEEK = auto()
    NEXT = auto()
    PREV = auto()
    CHUNK_FINISHED = auto()
    CHAPTER_FINISHED = auto()


@dataclass
class SeekRequest:
    """Seek请求"""
    position_ms: int
    chunk_index: Optional[int] = None
    offset_ms: int = 0


class PlaybackController:
    """
    播放控制器 - 核心状态机

    状态：STOPPED -> PLAYING -> PAUSED -> STOPPED
    """

    def __init__(self, config: dict = None):
        """
        初始化播放控制器

        Args:
            config: 配置字典
        """
        self.config = config or AUDIOBOOK_CONFIG

        # 核心组件
        self.chunk_manager = ChunkManager(self.config)
        self.tts_scheduler = get_tts_scheduler()
        self.audio_player = SimpleAudioPlayer()

        # 播放状态
        self.state = PlaybackState.STOPPED
        self.current_book: Optional[Book] = None
        self.current_chapter: Optional[Chapter] = None
        self.current_chunk_index: int = 0  # 全局索引
        self.current_chunk: Optional[TextChunk] = None

        # 事件队列
        self.event_queue: List[PlayerEvent] = []
        self.event_lock = threading.Lock()

        # 控制标志
        self._running = False
        self._stop_flag = threading.Event()

        # 回调
        self.on_chunk_changed: Optional[callable] = None
        self.on_chapter_changed: Optional[callable] = None
        self.on_state_changed: Optional[callable] = None
        self.on_progress: Optional[callable] = None

    def load_book(self, book_id: int, file_path: str = "") -> Book:
        """
        加载书籍

        Args:
            book_id: 书籍ID
            file_path: 文件路径

        Returns:
            Book对象
        """
        # 使用ChunkManager解析书籍
        book = self.chunk_manager.parse_book(file_path, book_id)
        self.current_book = book
        return book

    def play(self):
        """开始/恢复播放"""
        if not self.current_book:
            print("[PlaybackController] No book loaded")
            return

        if self.state == PlaybackState.PLAYING:
            return  # 已经在播放

        # 获取当前chunk
        chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if not chunk:
            print(f"[PlaybackController] Chunk {self.current_chunk_index} not found")
            return

        self.current_chunk = chunk

        # 检查音频是否准备好
        audio_path = self.chunk_manager.get_audio_path(
            self.current_book.book_id,
            chunk.chunk_id
        )

        if not Path(audio_path).exists() or Path(audio_path).stat().st_size < 20000:
            print(f"[PlaybackController] Audio not ready for chunk {chunk.chunk_id}")
            # 调度TTS
            self._schedule_urgent_chunks()
            return

        # 开始播放
        self.state = PlaybackState.PLAYING
        self._notify_state_changed()

        # 播放音频
        self.audio_player.play(
            audio_path,
            on_finished=self._on_chunk_finished
        )

        # 标记状态
        chunk.status = ChunkStatus.PLAYING

        # 调度后续chunks
        self._schedule_next_chunks()

        print(f"[PlaybackController] ▶ Playing chunk {chunk.chunk_id}")

    def pause(self):
        """暂停播放"""
        if self.state == PlaybackState.PLAYING:
            self.state = PlaybackState.PAUSED
            self.audio_player.pause()
            self._notify_state_changed()
            print("[PlaybackController] ⏸ Paused")

    def resume(self):
        """恢复播放"""
        if self.state == PlaybackState.PAUSED:
            self.state = PlaybackState.PLAYING
            self.audio_player.resume()
            self._notify_state_changed()
            print("[PlaybackController] ▶ Resumed")

    def stop(self):
        """停止播放"""
        self.state = PlaybackState.STOPPED
        self.audio_player.stop()
        self._notify_state_changed()
        print("[PlaybackController] ⏹ Stopped")

    def seek(self, chapter_index: int = None, chunk_index: int = None, offset_ms: int = 0):
        """
        Seek到指定位置

        Args:
            chapter_index: 章节索引
            chunk_index: chunk索引
            offset_ms: 偏移毫秒
        """
        if not self.current_book:
            return

        self.state = PlaybackState.SEEKING
        self._notify_state_changed()

        # 停止当前播放
        self.audio_player.stop()

        # 定位chunk
        if chunk_index is not None:
            self.current_chunk_index = chunk_index
        elif chapter_index is not None:
            chapter = self.current_book.chapters[chapter_index]
            self.current_chunk_index = chapter.start_index

        # 更新当前chunk
        chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if chunk:
            self.current_chunk = chunk
            self._notify_chunk_changed()

        # 检查音频是否准备好
        audio_path = self.chunk_manager.get_audio_path(
            self.current_book.book_id,
            chunk.chunk_id
        )

        if Path(audio_path).exists() and Path(audio_path).stat().st_size > 20000:
            # 音频已准备好，立即播放
            self.play()
        else:
            # 音频未准备好，调度TTS
            print(f"[PlaybackController] ⏳ Seeking to unready chunk {chunk.chunk_id}, scheduling TTS...")
            self._schedule_urgent_chunks()

    def next_chapter(self):
        """跳转到下一章"""
        if not self.current_book or not self.current_chapter:
            return

        # 找到下一章
        current_ch_idx = self.current_book.chapters.index(self.current_chapter)
        if current_ch_idx + 1 < len(self.current_book.chapters):
            next_chapter = self.current_book.chapters[current_ch_idx + 1]
            self.seek(chunk_index=next_chapter.start_index)
            print(f"[PlaybackController] ⏭ Next chapter: {next_chapter.title}")

    def prev_chapter(self):
        """跳转到上一章"""
        if not self.current_book or not self.current_chapter:
            return

        # 找到上一章
        current_ch_idx = self.current_book.chapters.index(self.current_chapter)
        if current_ch_idx > 0:
            prev_chapter = self.current_book.chapters[current_ch_idx - 1]
            self.seek(chunk_index=prev_chapter.start_index)
            print(f"[PlaybackController] ⏮ Prev chapter: {prev_chapter.title}")

    def _on_chunk_finished(self):
        """当前chunk播放完成"""
        if not self.current_chunk:
            return

        # 标记为完成
        self.current_chunk.status = ChunkStatus.DONE
        print(f"[PlaybackController] ✓ Chunk {self.current_chunk.chunk_id} finished")

        # 移动到下一个chunk
        self.current_chunk_index += 1

        # 检查是否到达章节末尾
        if self.current_chapter:
            if self.current_chunk_index >= self.current_chapter.end_index:
                # 章节播放完成
                self._on_chapter_finished()
                return

        # 检查是否到达书籍末尾
        if self.current_chunk_index >= self.current_book.total_chunks:
            print("[PlaybackController] 📚 Book finished")
            self.stop()
            return

        # 获取下一个chunk
        next_chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if not next_chunk:
            self.stop()
            return

        self.current_chunk = next_chunk
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
                on_finished=self._on_chunk_finished
            )
            next_chunk.status = ChunkStatus.PLAYING
            print(f"[PlaybackController] ▶ Playing chunk {next_chunk.chunk_id}")
        else:
            # 音频未准备好
            print(f"[PlaybackController] ⏳ Next chunk not ready, waiting...")
            # 调度紧急TTS
            self._schedule_urgent_chunks()
            # 暂停，等待TTS完成
            self.state = PlaybackState.PAUSED

    def _on_chapter_finished(self):
        """章节播放完成"""
        print(f"[PlaybackController] 📖 Chapter '{self.current_chapter.title}' finished")

        # 查找下一章
        current_ch_idx = self.current_book.chapters.index(self.current_chapter)
        if current_ch_idx + 1 < len(self.current_book.chapters):
            next_chapter = self.current_book.chapters[current_ch_idx + 1]
            self.current_chapter = next_chapter
            self._notify_chapter_changed()

            # 调度下一章TTS
            if self.config.get("auto_play_next_chapter", True):
                print(f"[PlaybackController] 🔄 Auto-playing next chapter...")
                # 继续播放，在_on_chunk_finished中会检查下一章
        else:
            print("[PlaybackController] 📚 Last chapter finished")
            self.stop()

    def _schedule_urgent_chunks(self):
        """调度紧急chunks（当前+预取）"""
        if not self.current_book:
            return

        # 获取当前章节
        chunk = self.current_book.get_chunk_by_index(self.current_chunk_index)
        if not chunk:
            return

        # 找到所属章节
        for chapter in self.current_book.chapters:
            if chapter.start_index <= self.current_chunk_index < chapter.end_index:
                # 调度当前章节
                self.tts_scheduler.schedule_chapter(
                    chapter,
                    self.current_book.book_id,
                    start_chunk_id=self.current_chunk_index
                )
                break

    def _schedule_next_chunks(self):
        """调度后续chunks（预合成）"""
        # 当前chunk的下一个
        prefetch = self.config.get("prefetch_chunks", 2)
        for i in range(1, prefetch + 1):
            next_idx = self.current_chunk_index + i
            if next_idx < self.current_book.total_chunks:
                chunk = self.current_book.get_chunk_by_index(next_idx)
                if chunk and chunk.status == ChunkStatus.PENDING:
                    self.tts_scheduler.schedule_chunk(
                        chunk,
                        self.current_book.book_id,
                        TaskPriority.HIGH if i <= 1 else TaskPriority.NORMAL
                    )

    def _notify_state_changed(self):
        """通知状态变化"""
        if self.on_state_changed:
            self.on_state_changed(self.state)

    def _notify_chunk_changed(self):
        """通知chunk变化"""
        if self.on_chunk_changed:
            self.on_chunk_changed(self.current_chunk)

    def _notify_chapter_changed(self):
        """通知章节变化"""
        if self.on_chapter_changed:
            self.on_chapter_changed(self.current_chapter)

    def _notify_progress(self, current_ms: int, total_ms: int):
        """通知播放进度"""
        if self.on_progress:
            self.on_progress(current_ms, total_ms)

    @property
    def progress_percent(self) -> float:
        """播放进度百分比"""
        if not self.current_book:
            return 0.0
        return self.current_book.progress_percent

    def get_position_ms(self) -> int:
        """获取当前播放位置（毫秒）"""
        # TODO: 实现位置跟踪
        return 0

    def get_duration_ms(self) -> int:
        """获取总时长（毫秒）"""
        if not self.current_book:
            return 0
        return self.current_book.current_chapter.total_duration_ms if self.current_book.current_chapter else 0


from pathlib import Path
