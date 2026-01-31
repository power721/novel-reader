"""
关于对话框 - 显示应用信息
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("关于 Novel Reader")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("Novel Reader")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本
        version_label = QLabel("版本 0.1.0")
        version_label.setStyleSheet("font-size: 14px;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 描述
        desc_label = QLabel(
            "本地有声书管理器\n\n"
            "支持文本转语音和音频播放"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)

        # 功能特点
        features_label = QLabel(
            "功能特点:\n"
            "• 完全离线\n"
            "• SQLite 数据库\n"
            "• TTS 转换\n"
            "• 断点续播\n"
            "• 拖拽导入书籍\n\n"
            "使用 PySide6 构建"
        )
        features_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(features_label)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
