"""
播放控制组件 - 播放控制按钮和进度显示
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Optional


class PlayerWidget(QWidget):
    """播放控制组件"""

    # 信号定义
    play_requested = Signal(int)  # 请求播放，参数：book_id
    play_from_chunk_requested = Signal(int, int)  # 请求从指定位置播放，参数：book_id, chunk
    stop_requested = Signal()  # 请求停止播放
    play_previous_chapter_requested = Signal()  # 请求播放上一章
    play_next_chapter_requested = Signal()  # 请求播放下一章

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.is_playing = False

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 播放控制分组
        player_group = QGroupBox("▶️ 播放控制")
        player_group.setStyleSheet("""
        QGroupBox::title {
            padding-right: 6px;
        }
        """)
        player_layout = QVBoxLayout()

        # 播放按钮行
        control_layout = QHBoxLayout()

        self.prev_chapter_btn = QPushButton("⏮ 上一章")
        self.prev_chapter_btn.setStyleSheet("padding: 8px 12px;")
        self.prev_chapter_btn.clicked.connect(self._on_prev_chapter_clicked)

        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setStyleSheet("padding: 8px 16px;")
        self.play_btn.clicked.connect(self._on_play_clicked)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setStyleSheet("padding: 8px 16px;")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)

        self.next_chapter_btn = QPushButton("⏭ 下一章")
        self.next_chapter_btn.setStyleSheet("padding: 8px 12px;")
        self.next_chapter_btn.clicked.connect(self._on_next_chapter_clicked)

        control_layout.addWidget(self.prev_chapter_btn)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.next_chapter_btn)
        control_layout.addStretch()

        player_layout.addLayout(control_layout)

        # 播放进度行
        progress_layout = QHBoxLayout()

        progress_label = QLabel("播放进度:")
        progress_layout.addWidget(progress_label)

        self.playback_progress = QProgressBar()
        self.playback_progress.setRange(0, 100)
        self.playback_progress.setValue(0)
        progress_layout.addWidget(self.playback_progress)

        self.playback_status_label = QLabel("未播放")
        self.playback_status_label.setMinimumWidth(100)
        progress_layout.addWidget(self.playback_status_label)

        player_layout.addLayout(progress_layout)

        player_group.setLayout(player_layout)
        layout.addWidget(player_group)

    def _on_play_clicked(self):
        """播放按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if self.is_playing:
            QMessageBox.information(self, "提示", "正在播放中，请先停止")
            return

        self.play_requested.emit(self.current_book_id)

    def _on_stop_clicked(self):
        """停止按钮点击事件"""
        self.stop_requested.emit()

    def _on_prev_chapter_clicked(self):
        """上一章按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return
        self.play_previous_chapter_requested.emit()

    def _on_next_chapter_clicked(self):
        """下一章按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return
        self.play_next_chapter_requested.emit()

    def set_book(self, book_id: int):
        """设置当前书籍"""
        self.current_book_id = book_id

    def set_playing_state(self, is_playing: bool):
        """设置播放状态"""
        self.is_playing = is_playing
        self.play_btn.setEnabled(not is_playing)
        self.stop_btn.setEnabled(is_playing)

        if is_playing:
            self.playback_status_label.setText("正在播放...")
        else:
            self.playback_status_label.setText("未播放")
            self.playback_progress.setValue(0)

    def set_progress(self, current: int, total: int):
        """设置播放进度"""
        if total > 0:
            progress = int(current / total * 100)
            self.playback_progress.setValue(progress)
            self.playback_status_label.setText(f"{current}/{total}")

    def reset(self):
        """重置状态"""
        self.current_book_id = None
        self.is_playing = False
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.playback_progress.setValue(0)
        self.playback_status_label.setText("未播放")
