"""
PySide6 GUI 组件模块

包含所有自定义 GUI 组件
"""

from .book_list_widget import BookListWidget
from .chapter_list_widget import ChapterListWidget
from .play_text_widget import PlayTextWidget
from .player_widget import PlayerWidget
from .tts_widget import TTSWidget

__all__ = [
    "BookListWidget",
    "ChapterListWidget",
    "PlayTextWidget",
    "PlayerWidget",
    "TTSWidget",
]
