"""
TTS 转换组件 - TTS 转换控制和进度显示
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal
from typing import Optional


class TTSWidget(QWidget):
    """TTS 转换组件"""

    # 信号定义
    convert_book_requested = Signal(int)  # 请求转换书籍，参数：book_id
    convert_chapter_requested = Signal(int, int)  # 请求转换章节，参数：book_id, chapter_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.is_converting = False

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # TTS 转换分组
        tts_group = QGroupBox("🎙️ TTS 转换")
        tts_group.setStyleSheet("""
                QGroupBox::title {
                    padding-right: 6px;
                }
                """)
        tts_layout = QVBoxLayout()

        # 控制按钮行
        control_layout = QHBoxLayout()

        self.convert_book_btn = QPushButton("转换整本书")
        self.convert_book_btn.setStyleSheet("padding: 6px 12px;")
        self.convert_book_btn.clicked.connect(self._on_convert_book_clicked)

        self.convert_chapter_btn = QPushButton("转换指定范围")
        self.convert_chapter_btn.setStyleSheet("padding: 6px 12px;")
        self.convert_chapter_btn.clicked.connect(self._on_convert_chapter_clicked)

        control_layout.addWidget(self.convert_book_btn)
        control_layout.addWidget(self.convert_chapter_btn)
        control_layout.addStretch()

        # tts_layout.addLayout(control_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        tts_layout.addWidget(self.progress)

        # 状态标签
        self.status_label = QLabel("就绪")
        tts_layout.addWidget(self.status_label)

        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("转换日志将显示在这里...")
        tts_layout.addWidget(self.log_text)

        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

    def _on_convert_book_clicked(self):
        """转换整本书按钮点击事件"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        if self.is_converting:
            QMessageBox.information(self, "提示", "正在转换中，请稍候")
            return

        # 确认开始转换
        reply = QMessageBox.question(
            self,
            "确认转换",
            "确定要开始 TTS 转换吗？\n这可能需要较长时间。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.convert_book_requested.emit(self.current_book_id)

    def _on_convert_chapter_clicked(self):
        """转换指定范围按钮点击事件"""
        QMessageBox.information(self, "提示", "功能开发中...\n可使用「转换整本书」功能")

    def set_book(self, book_id: int):
        """设置当前书籍"""
        self.current_book_id = book_id

    def set_converting_state(self, is_converting: bool):
        """设置转换状态"""
        self.is_converting = is_converting
        self.convert_book_btn.setEnabled(not is_converting)
        self.convert_chapter_btn.setEnabled(not is_converting)

        if is_converting:
            self.status_label.setText("正在转换...")
        else:
            self.status_label.setText("转换完成")

    def set_progress(self, current: int, total: int):
        """设置转换进度"""
        if total > 0:
            progress = int(current / total * 100)
            self.progress.setValue(progress)
            self.status_label.setText(f"转换中: {current}/{total} ({progress}%)")

    def add_log(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def reset(self):
        """重置状态"""
        self.current_book_id = None
        self.is_converting = False
        self.convert_book_btn.setEnabled(True)
        self.convert_chapter_btn.setEnabled(True)
        self.progress.setValue(0)
        self.status_label.setText("就绪")
