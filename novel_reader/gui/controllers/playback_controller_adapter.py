"""
PlaybackController GUI适配器

将新的PlaybackController架构连接到PySide6 GUI
"""
from PySide6.QtCore import QObject, Signal, Slot
from typing import Optional
from pathlib import Path

from novel_reader.core.playback_controller_v2 import (
    PlaybackController,
    PlaybackState,
    PlayerConfig,
    TTSConfig
)
from novel_reader.core.models_v2 import Book, Chapter, TextChunk


class PlaybackControllerAdapter(QObject):
    """
    PlaybackController的GUI适配器

    将PlaybackController的回调转换为Qt信号
    """

    # 状态变化信号
    state_changed = Signal(str)  # STOPPED/PLAYING/PAUSED/SEEKING
    chunk_changed = Signal(int)  # chunk_id
    chapter_changed = Signal(int, str)  # chapter_id, chapter_title
    progress_updated = Signal(int, int)  # current_ms, total_ms
    book_finished = Signal()

    # 错误信号
    error_occurred = Signal(str)

    # TTS进度信号
    tts_progress = Signal(str, int, int)  # status, current, total

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controller: Optional[PlaybackController] = None
        self.current_book_id: Optional[int] = None

        # 配置
        self.config = PlayerConfig()
        self.tts_config = TTSConfig()

    def initialize(self):
        """初始化控制器"""
        print(f"[PlaybackControllerAdapter] DEBUG: initialize() called")

        self.controller = PlaybackController(
            config=self.config,
            tts_config=self.tts_config
        )
        print(f"[PlaybackControllerAdapter] DEBUG: Controller created")

        # 连接回调
        self.controller.on_state_changed = self._on_state_changed
        self.controller.on_chunk_changed = self._on_chunk_changed
        self.controller.on_chapter_changed = self._on_chapter_changed
        self.controller.on_progress = self._on_progress
        self.controller.on_book_finished = self._on_book_finished
        print(f"[PlaybackControllerAdapter] DEBUG: Callbacks connected")

        # 启动控制器
        self.controller.start()
        print(f"[PlaybackControllerAdapter] DEBUG: Controller started")

    def shutdown(self):
        """关闭控制器"""
        if self.controller:
            self.controller.stop()
            self.controller = None

    def load_book(self, book_id: int, file_path: str) -> Book:
        """加载书籍"""
        self.current_book_id = book_id
        return self.controller.load_book(book_id, file_path)

    def play(self):
        """播放"""
        print(f"[PlaybackControllerAdapter] DEBUG: play() called")
        if self.controller:
            print(f"[PlaybackControllerAdapter] DEBUG: Controller exists, calling controller.play()")
            self.controller.play()
        else:
            print(f"[PlaybackControllerAdapter] ERROR: Controller is None!")

    def pause(self):
        """暂停"""
        print(f"[PlaybackControllerAdapter] DEBUG: pause() called")
        if self.controller:
            self.controller.pause()

    def resume(self):
        """恢复播放"""
        print(f"[PlaybackControllerAdapter] DEBUG: resume() called")
        if self.controller:
            self.controller.resume()

    def stop(self):
        """停止播放"""
        print(f"[PlaybackControllerAdapter] DEBUG: stop() called")
        if self.controller:
            self.controller.stop()

    def next_chapter(self):
        """下一章"""
        if self.controller:
            self.controller.next_chapter()

    def prev_chapter(self):
        """上一章"""
        if self.controller:
            self.controller.prev_chapter()

    def seek_to_chapter(self, chapter_index: int):
        """跳转到指定章节"""
        if self.controller:
            self.controller.seek_to_chapter(chapter_index)

    def seek_to_chunk(self, chunk_index: int):
        """跳转到指定chunk"""
        if self.controller:
            self.controller.seek(chunk_index=chunk_index)

    # ==================== 回调处理函数 ====================

    def _on_state_changed(self, state: PlaybackState):
        """状态变化回调"""
        print(f"[PlaybackControllerAdapter] DEBUG: _on_state_changed() called with state={state.name}")
        self.state_changed.emit(state.name)

    def _on_chunk_changed(self, chunk: TextChunk):
        """chunk变化回调"""
        self.chunk_changed.emit(chunk.chunk_id)

    def _on_chapter_changed(self, chapter: Chapter):
        """章节变化回调"""
        self.chapter_changed.emit(chapter.chapter_id, chapter.title)

    def _on_progress(self, current_ms: int, total_ms: int):
        """进度回调"""
        self.progress_updated.emit(current_ms, total_ms)

    def _on_book_finished(self):
        """书籍播放完成回调"""
        self.book_finished.emit()

    # ==================== 属性访问 ====================

    @property
    def state(self) -> PlaybackState:
        """获取当前状态"""
        if self.controller:
            return self.controller.state
        return PlaybackState.STOPPED

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        if self.controller:
            return self.controller.is_playing
        return False

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        if self.controller:
            return self.controller.is_paused
        return False

    @property
    def current_book(self) -> Optional[Book]:
        """获取当前书籍"""
        if self.controller:
            return self.controller.current_book
        return None

    @property
    def current_chapter(self) -> Optional[Chapter]:
        """获取当前章节"""
        if self.controller:
            return self.controller.current_chapter
        return None

    @property
    def current_chunk(self) -> Optional[TextChunk]:
        """获取当前chunk"""
        if self.controller:
            return self.controller.current_chunk
        return None
