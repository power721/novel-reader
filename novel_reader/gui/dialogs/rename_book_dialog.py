"""
重命名书籍对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class RenameBookDialog(QDialog):
    """重命名书籍对话框"""

    def __init__(self, current_title: str, parent=None):
        super().__init__(parent)

        self.current_title = current_title
        self.new_title = ""

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.setWindowTitle("重命名书籍")
        self.setModal(True)
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 说明标签
        info_label = QLabel("请输入新的书名:")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        # 当前书名
        current_label = QLabel(f"当前书名: {self.current_title}")
        current_label.setStyleSheet("color: #666; padding: 5px;")
        current_label.setWordWrap(True)
        layout.addWidget(current_label)

        # 输入框
        self.title_input = QLineEdit(self.current_title)
        self.title_input.setMinimumHeight(35)
        self.title_input.selectAll()
        layout.addWidget(self.title_input)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setMinimumWidth(100)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok_clicked)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _on_ok_clicked(self):
        """确定按钮点击事件"""
        new_title = self.title_input.text().strip()

        if not new_title:
            QMessageBox.warning(self, "警告", "书名不能为空")
            return

        if new_title == self.current_title:
            QMessageBox.information(self, "提示", "书名未改变")
            self.reject()
            return

        self.new_title = new_title
        self.accept()

    def get_new_title(self) -> str:
        """获取输入的新书名"""
        return self.new_title


def rename_book_dialog(parent, current_title: str) -> str:
    """
    显示重命名对话框

    Args:
        parent: 父窗口
        current_title: 当前书名

    Returns:
        新书名，如果取消则返回空字符串
    """
    dialog = RenameBookDialog(current_title, parent)
    result = dialog.exec()

    if result == QDialog.Accepted:
        return dialog.get_new_title()

    return ""
