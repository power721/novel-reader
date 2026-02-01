"""
当前播放文本组件 - 显示当前正在播放的文本内容
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from typing import Optional


class BookmarkListWidget(QWidget):
    """当前播放文本组件"""

    # 信号定义
    bookmark_double_clicked = Signal(int)  # 保留信号以兼容现有代码

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("📝 当前播放文本")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 当前播放文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlainText("未播放")
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Microsoft YaHei UI', 'SimHei', sans-serif;
                font-size: 14px;
                line-height: 1.8;
            }
        """)
        layout.addWidget(self.text_display)

    def update_current_text(self, book_id: int, chunk_id: int):
        """
        更新当前播放的文本

        Args:
            book_id: 书籍ID
            chunk_id: 当前播放的chunk ID
        """
        self.current_book_id = book_id

        if book_id is None:
            self.text_display.setPlainText("未选择书籍")
            return

        try:
            from novel_reader.core import get_book
            from novel_reader.utils import load_txt_file, parse_txt

            book = get_book(book_id)
            if book is None:
                self.text_display.setPlainText("书籍不存在")
                return

            if not isinstance(book, dict):
                self.text_display.setPlainText(f"错误: book类型为 {type(book)}")
                return

            # 加载文本
            text = load_txt_file(book['file_path'])
            chunks, chapters = parse_txt(text)

            if chunk_id < 0 or chunk_id >= len(chunks):
                self.text_display.setPlainText(f"Chunk {chunk_id} 超出范围")
                return

            # 获取前两个、当前和后两个chunk的文本
            prev_texts = []
            for i in range(2):
                offset = i + 1
                if chunk_id - offset >= 0:
                    prev_texts.insert(0, chunks[chunk_id - offset])

            current_text = chunks[chunk_id]

            next_texts = []
            for i in range(2):
                if chunk_id + i + 1 < len(chunks):
                    next_texts.append(chunks[chunk_id + i + 1])

            # 构建HTML显示，高亮当前chunk
            html_content = "<html><body style='background-color: #f5f5f5;'>"

            # 前两个chunk（灰色小字）
            for prev_text in prev_texts:
                escaped_prev = prev_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_content += f"<div style='color: #999; font-size: 13px; margin-bottom: 8px;'>{escaped_prev}</div>"

            # 当前chunk（黑色大字，高亮背景）- 添加锚点用于滚动定位
            escaped_current = current_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_content += "<a name='current'></a>"
            html_content += f"<div style='background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 10px 0; border-radius: 4px;'>"
            html_content += f"<div style='color: #000; font-size: 15px; font-weight: 500;'>{escaped_current}</div>"
            html_content += "</div>"

            # 后两个chunk（灰色小字）
            for next_text in next_texts:
                escaped_next = next_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_content += f"<div style='color: #999; font-size: 13px; margin-top: 8px;'>{escaped_next}</div>"

            html_content += "</body></html>"

            self.text_display.setHtml(html_content)

            # 滚动到顶部，让当前chunk可见
            self.text_display.verticalScrollBar().setValue(self.text_display.verticalScrollBar().minimum())

            # 滚动到顶部
            cursor = self.text_display.textCursor()
            cursor.setPosition(0)
            self.text_display.setTextCursor(cursor)

        except Exception as e:
            self.text_display.setPlainText(f"加载失败: {str(e)}")

    def load_bookmarks(self, book_id: int):
        """兼容原有接口，现在只更新显示"""
        self.current_book_id = book_id
        if book_id is None:
            self.text_display.setPlainText("未播放")

    def clear(self):
        """清空显示"""
        self.text_display.setPlainText("未播放")
        self.current_book_id = None
