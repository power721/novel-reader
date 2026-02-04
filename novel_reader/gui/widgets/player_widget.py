"""
播放控制组件 - 播放控制按钮和进度显示
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QMessageBox, QFrame, QSlider, QComboBox
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
    volume_changed = Signal(float)  # 音量变化，参数：volume (0.0 - 1.0)
    playback_speed_changed = Signal(float)  # 播放速度变化，参数：speed (0.5 - 2.0)

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

        info_widget = QWidget()
        info_widget.setFixedHeight(60)

        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(8, 6, 8, 6)
        info_layout.setSpacing(6)
        info_layout.setAlignment(Qt.AlignTop)

        info_label = QLabel("📖 正在播放:")
        info_label.setStyleSheet("font-weight: bold;")
        info_label.setAlignment(Qt.AlignTop)
        info_layout.addWidget(info_label, 0, Qt.AlignTop)

        play_layout = QVBoxLayout()
        play_layout.setSpacing(2)

        self.current_book_label = QLabel("未选择书籍")
        self.current_book_label.setWordWrap(True)
        play_layout.addWidget(self.current_book_label)

        self.current_chapter_label = QLabel("未选择章节")
        self.current_chapter_label.setWordWrap(True)
        play_layout.addWidget(self.current_chapter_label)

        info_layout.addLayout(play_layout, 1)
        info_layout.setAlignment(play_layout, Qt.AlignTop)

        player_layout.addWidget(info_widget)

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
        self.play_btn.clicked.connect(self._on_play_clicked)

        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setStyleSheet("padding: 8px 16px;")
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)  # 初始禁用

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setStyleSheet("padding: 8px 16px;")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)  # 初始禁用

        self.next_chapter_btn = QPushButton("⏭ 下一章")
        self.next_chapter_btn.setStyleSheet("padding: 8px 12px;")
        self.next_chapter_btn.clicked.connect(self._on_next_chapter_clicked)

        control_layout.addWidget(self.prev_chapter_btn)
        control_layout.addWidget(self.play_btn)
        # control_layout.addWidget(self.pause_btn)
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

        # 音量控制行
        volume_layout = QHBoxLayout()

        volume_label = QLabel("🔊 音量:")
        volume_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)

        self.volume_value_label = QLabel("100%")
        self.volume_value_label.setMinimumWidth(40)
        volume_layout.addWidget(self.volume_value_label)

        volume_layout.addStretch()
        player_layout.addLayout(volume_layout)

        # 播放速度控制行
        speed_layout = QHBoxLayout()

        speed_label = QLabel("⏩ 速度:")
        speed_layout.addWidget(speed_label)

        # 播放速度滑块
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)  # 0.5x
        self.speed_slider.setMaximum(200)  # 2.0x
        self.speed_slider.setValue(100)  # 1.0x
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(25)  # 每 0.25x 一个刻度
        self.speed_slider.setSingleStep(5)  # 步长 0.05x
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)

        # 速度显示标签
        self.speed_value_label = QLabel("1.00x")
        self.speed_value_label.setMinimumWidth(45)
        self.speed_value_label.setAlignment(Qt.AlignCenter)
        speed_layout.addWidget(self.speed_value_label)

        # 预设速度按钮
        self.speed_preset_0_5_btn = QPushButton("0.5x")
        self.speed_preset_0_5_btn.setStyleSheet("padding: 4px 8px; font-size: 10px;")
        self.speed_preset_0_5_btn.clicked.connect(lambda: self._set_speed(0.5))
        speed_layout.addWidget(self.speed_preset_0_5_btn)

        self.speed_preset_1_0_btn = QPushButton("1.0x")
        self.speed_preset_1_0_btn.setStyleSheet("padding: 4px 8px; font-size: 10px;")
        self.speed_preset_1_0_btn.clicked.connect(lambda: self._set_speed(1.0))
        speed_layout.addWidget(self.speed_preset_1_0_btn)

        self.speed_preset_1_25_btn = QPushButton("1.25x")
        self.speed_preset_1_25_btn.setStyleSheet("padding: 4px 8px; font-size: 10px;")
        self.speed_preset_1_25_btn.clicked.connect(lambda: self._set_speed(1.25))
        speed_layout.addWidget(self.speed_preset_1_25_btn)

        self.speed_preset_1_5_btn = QPushButton("1.5x")
        self.speed_preset_1_5_btn.setStyleSheet("padding: 4px 8px; font-size: 10px;")
        self.speed_preset_1_5_btn.clicked.connect(lambda: self._set_speed(1.5))
        speed_layout.addWidget(self.speed_preset_1_5_btn)

        self.speed_preset_2_0_btn = QPushButton("2.0x")
        self.speed_preset_2_0_btn.setStyleSheet("padding: 4px 8px; font-size: 10px;")
        self.speed_preset_2_0_btn.clicked.connect(lambda: self._set_speed(2.0))
        speed_layout.addWidget(self.speed_preset_2_0_btn)

        speed_layout.addStretch()
        player_layout.addLayout(speed_layout)

        # 播放进度行 - 本章进度
        chapter_progress_layout = QHBoxLayout()

        chapter_progress_label = QLabel("本章进度:")
        chapter_progress_layout.addWidget(chapter_progress_label)

        self.chapter_progress = QProgressBar()
        self.chapter_progress.setRange(0, 100)
        self.chapter_progress.setValue(0)
        chapter_progress_layout.addWidget(self.chapter_progress)

        self.chapter_progress_status_label = QLabel("未播放")
        self.chapter_progress_status_label.setMinimumWidth(100)
        chapter_progress_layout.addWidget(self.chapter_progress_status_label)

        player_layout.addLayout(chapter_progress_layout)

        # 播放进度行 - 全书进度
        book_progress_layout = QHBoxLayout()

        book_progress_label = QLabel("全书进度:")
        book_progress_layout.addWidget(book_progress_label)

        self.book_progress = QProgressBar()
        self.book_progress.setRange(0, 100)
        self.book_progress.setValue(0)
        book_progress_layout.addWidget(self.book_progress)

        self.book_progress_status_label = QLabel("未播放")
        self.book_progress_status_label.setMinimumWidth(100)
        book_progress_layout.addWidget(self.book_progress_status_label)

        player_layout.addLayout(book_progress_layout)

        player_group.setLayout(player_layout)
        layout.addWidget(player_group)

    def _on_play_clicked(self):
        """播放按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if not self.is_playing:
            self.play_requested.emit(self.current_book_id)

    def _on_pause_clicked(self):
        """暂停按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if self.is_paused:
            # 已暂停，恢复播放
            self.resume_requested.emit()
        elif self.is_playing:
            # 正在播放，暂停
            self.pause_requested.emit()

    def _on_stop_clicked(self):
        """停止按钮点击事件"""
        self.stop_requested.emit()

    def _on_play_stop_clicked(self):
        """播放/停止按钮点击事件（保留兼容性）"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if self.is_playing:
            self.stop_requested.emit()
        else:
            self.play_requested.emit(self.current_book_id)

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

    def _on_volume_changed(self, value: int):
        """音量滑块变化事件"""
        volume = value / 100.0
        self.volume_value_label.setText(f"{value}%")
        self.volume_changed.emit(volume)

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量值 (0.0 - 1.0)
        """
        value = int(max(0, min(100, volume * 100)))
        self.volume_slider.setValue(value)
        self.volume_value_label.setText(f"{value}%")

    def get_volume(self) -> float:
        """
        获取当前音量

        Returns:
            音量值 (0.0 - 1.0)
        """
        return self.volume_slider.value() / 100.0

    def _on_speed_slider_changed(self, value: int):
        """播放速度滑块变化事件"""
        speed = value / 100.0
        self.speed_value_label.setText(f"{speed:.2f}x")
        self.playback_speed_changed.emit(speed)

    def _set_speed(self, speed: float):
        """设置播放速度（预设按钮使用）"""
        self.set_playback_speed(speed)
        self.playback_speed_changed.emit(speed)

    def set_playback_speed(self, speed: float):
        """
        设置播放速度

        Args:
            speed: 播放速度 (0.5 - 2.0)
        """
        speed = max(0.5, min(2.0, speed))
        value = int(round(speed * 100))
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(value)
        self.speed_slider.blockSignals(False)
        self.speed_value_label.setText(f"{speed:.2f}x")

    def get_playback_speed(self) -> float:
        """
        获取当前播放速度

        Returns:
            播放速度 (0.5 - 2.0)
        """
        return self.speed_slider.value() / 100.0

    def set_book(self, book_id: int, book_title: str = ""):
        """设置当前书籍（不更新显示）"""
        self.current_book_id = book_id
        # 点击书籍时不更新current_book_label，只有播放时才更新

    def update_current_playback(self, book_title: str, chapter_title: str):
        """更新当前播放信息"""
        self._update_current_display(book_title, chapter_title)

    def _update_current_display(self, book_title: str = "", chapter_title: str = ""):
        """更新当前显示标签"""
        # 存储书名和章节标题，用于状态栏显示
        self.current_book_title = book_title
        self.current_chapter_title = chapter_title

        if book_title or chapter_title:
            self.current_book_label.setText(book_title)
            self.current_chapter_label.setText(chapter_title)
            self.current_book_label.setStyleSheet("color: #222;font-weight: 600;")
            self.current_chapter_label.setStyleSheet("color: rgba(0, 0, 0, 0.55);")
        else:
            self.current_book_label.setText("未选择书籍")
            self.current_chapter_label.setText("未选择章节")
            self.current_book_label.setStyleSheet("color: #222; font-style: italic;")
            self.current_chapter_label.setStyleSheet("color: rgba(0, 0, 0, 0.55); font-style: italic;")

    def set_playing_state(self, is_playing: bool):
        """设置播放状态"""
        self.is_playing = is_playing
        self.play_btn.setEnabled(not is_playing)  # 播放时禁用播放按钮
        self.pause_btn.setEnabled(is_playing)  # 播放时启用暂停按钮
        self.stop_btn.setEnabled(is_playing)  # 播放时启用停止按钮

        if is_playing:
            self.play_btn.setText("▶ 播放")
            self.pause_btn.setText("⏸ 暂停")
        else:
            self.is_paused = False
            self.play_btn.setText("▶ 播放")
            self.play_btn.setEnabled(True)
            self.pause_btn.setText("⏸ 暂停")
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            # 停止时保留进度显示，不重置
            # self.chapter_progress_status_label.setText("未播放")
            # self.book_progress_status_label.setText("未播放")
            # self.chapter_progress.setValue(0)
            # self.book_progress.setValue(0)
            # 停止时禁用分段导航按钮
            self.prev_chunk_btn.setEnabled(False)
            self.next_chunk_btn.setEnabled(False)

    def set_paused_state(self, is_paused: bool):
        """设置暂停状态"""
        self.is_paused = is_paused
        self.is_playing = not is_paused

        self.play_btn.setEnabled(is_paused)  # 暂停时可以点击播放来恢复

        if is_paused:
            self.pause_btn.setText("▶ 继续")
            self.play_btn.setEnabled(False)
        else:
            self.pause_btn.setText("⏸ 暂停")

    def set_progress(self, current: int, total: int):
        """设置播放进度（保留兼容性）"""
        if total > 0:
            progress = int(current / total * 100)
            self.book_progress.setValue(progress)
            self.book_progress_status_label.setText(f"{current}/{total}")

    def set_dual_progress(self, current_chunk: int, chapter_start: int, chapter_end: int, total_chunks: int):
        """设置章节和全书进度"""
        # 设置本章进度
        if chapter_end > chapter_start:
            chapter_current = current_chunk - chapter_start
            chapter_total = chapter_end - chapter_start
            chapter_progress = int(chapter_current / chapter_total * 100) if chapter_total > 0 else 0
            self.chapter_progress.setValue(chapter_progress)
            self.chapter_progress_status_label.setText(f"{chapter_current}/{chapter_total}")
        else:
            self.chapter_progress.setValue(100)
            self.chapter_progress_status_label.setText("1/1")

        # 设置全书进度
        if total_chunks > 0:
            book_progress = int(current_chunk / total_chunks * 100)
            self.book_progress.setValue(book_progress)
            self.book_progress_status_label.setText(f"{current_chunk}/{total_chunks}")

        # 更新后退/前进按钮状态
        self.prev_chunk_btn.setEnabled(current_chunk > 0)
        self.next_chunk_btn.setEnabled(current_chunk < total_chunks - 1)

    def reset(self):
        """重置状态"""
        self.current_book_id = None
        self.is_playing = False
        self.is_paused = False
        self.play_btn.setText("▶ 播放")
        self.play_btn.setEnabled(True)
        self.pause_btn.setText("⏸ 暂停")
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.chapter_progress.setValue(0)
        self.chapter_progress_status_label.setText("未播放")
        self.book_progress.setValue(0)
        self.book_progress_status_label.setText("未播放")
        # 重置播放信息显示
        self._update_current_display()
        # 重置分段导航按钮
        self.prev_chunk_btn.setEnabled(False)
        self.next_chunk_btn.setEnabled(False)
