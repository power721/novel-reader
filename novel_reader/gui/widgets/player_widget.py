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
    pause_requested = Signal()  # 请求暂停播放
    resume_requested = Signal()  # 请求恢复播放
    stop_requested = Signal()  # 请求停止播放
    play_previous_chapter_requested = Signal()  # 请求播放上一章
    play_next_chapter_requested = Signal()  # 请求播放下一章
    play_previous_chunk_requested = Signal()  # 请求播放上一分段
    play_next_chunk_requested = Signal()  # 请求播放下一分段

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.is_playing = False
        self.is_paused = False

        # 存储当前播放信息
        self.current_book_title = ""
        self.current_chapter_title = ""

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

        # 当前播放信息行 (永久显示)
        info_layout = QHBoxLayout()
        info_label = QLabel("📖 正在播放:")
        info_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(info_label)

        # 当前书籍和章节显示
        self.current_book_label = QLabel("未选择书籍")
        self.current_book_label.setStyleSheet("color: #555; padding: 5px;")
        self.current_book_label.setWordWrap(True)
        info_layout.addWidget(self.current_book_label)
        info_layout.addStretch()

        player_layout.addLayout(info_layout)

        # 分隔线
        from PySide6.QtWidgets import QFrame
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        player_layout.addWidget(separator)

        # 播放按钮行
        control_layout = QHBoxLayout()

        self.prev_chapter_btn = QPushButton("⏮ 上一章")
        self.prev_chapter_btn.setStyleSheet("padding: 8px 12px;")
        self.prev_chapter_btn.clicked.connect(self._on_prev_chapter_clicked)

        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setStyleSheet("padding: 8px 16px;")
        self.play_btn.clicked.connect(self._on_play_pause_clicked)

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

        # 分段导航按钮行
        chunk_nav_layout = QHBoxLayout()

        self.prev_chunk_btn = QPushButton("◀ 后退")
        self.prev_chunk_btn.setStyleSheet("padding: 6px 10px; font-size: 11px;")
        self.prev_chunk_btn.clicked.connect(self._on_prev_chunk_clicked)

        chunk_label = QLabel("分段导航:")
        chunk_label.setStyleSheet("color: #666; font-size: 11px;")

        self.next_chunk_btn = QPushButton("前进 ▶")
        self.next_chunk_btn.setStyleSheet("padding: 6px 10px; font-size: 11px;")
        self.next_chunk_btn.clicked.connect(self._on_next_chunk_clicked)

        chunk_nav_layout.addStretch()
        chunk_nav_layout.addWidget(self.prev_chunk_btn)
        chunk_nav_layout.addWidget(chunk_label)
        chunk_nav_layout.addWidget(self.next_chunk_btn)
        chunk_nav_layout.addStretch()

        player_layout.addLayout(chunk_nav_layout)

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

    def _on_play_pause_clicked(self):
        """播放/暂停按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if self.is_playing:
            # 正在播放，暂停
            self.pause_requested.emit()
        elif self.is_paused:
            # 已暂停，恢复
            self.resume_requested.emit()
        else:
            # 未播放，开始播放
            self.play_requested.emit(self.current_book_id)

    def _on_play_clicked(self):
        """播放按钮点击事件（保留兼容性）"""
        self._on_play_pause_clicked()

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

    def _on_prev_chunk_clicked(self):
        """上一分段按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return
        self.play_previous_chunk_requested.emit()

    def _on_next_chunk_clicked(self):
        """下一分段按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return
        self.play_next_chunk_requested.emit()

    def set_book(self, book_id: int, book_title: str = ""):
        """设置当前书籍"""
        self.current_book_id = book_id
        # 不立即更新显示，只在播放时更新

    def update_current_playback(self, book_title: str, chapter_title: str):
        """更新当前播放信息"""
        self._update_current_display(book_title, chapter_title)

    def _update_current_display(self, book_title: str = "", chapter_title: str = ""):
        """更新当前显示标签"""
        # 存储书名和章节标题，用于状态栏显示
        self.current_book_title = book_title
        self.current_chapter_title = chapter_title

        if book_title or chapter_title:
            # 显示书名和章节
            if book_title and chapter_title:
                text = f"{book_title} - {chapter_title}"
            elif book_title:
                text = book_title
            else:
                text = chapter_title

            self.current_book_label.setText(text)
            self.current_book_label.setStyleSheet(
                "color: #0066cc; padding: 5px; font-weight: bold;"
            )
        elif self.current_book_id:
            # 只有book_id，尝试获取标题
            self.current_book_label.setText(f"书籍 ID: {self.current_book_id}")
            self.current_book_label.setStyleSheet(
                "color: #555; padding: 5px;"
            )
        else:
            # 未选择
            self.current_book_label.setText("未选择书籍")
            self.current_book_label.setStyleSheet(
                "color: #999; padding: 5px; font-style: italic;"
            )

    def set_playing_state(self, is_playing: bool):
        """设置播放状态"""
        self.is_playing = is_playing
        self.is_paused = False
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(is_playing)

        if is_playing:
            self.play_btn.setText("⏸ 暂停")
        else:
            self.play_btn.setText("▶ 播放")
            self.playback_status_label.setText("未播放")
            self.playback_progress.setValue(0)

    def set_paused_state(self, is_paused: bool):
        """设置暂停状态"""
        self.is_paused = is_paused
        self.is_playing = not is_paused

        if is_paused:
            self.play_btn.setText("▶ 继续")
        else:
            self.play_btn.setText("⏸ 暂停")

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
        self.is_paused = False
        self.play_btn.setText("▶ 播放")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.playback_progress.setValue(0)
        self.playback_status_label.setText("未播放")
        # 重置播放信息显示
        self._update_current_display()
