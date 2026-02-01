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
                font-size: 13px;
                line-height: 1.6;
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

            # 获取当前chunk的文本
            current_chunk_text = chunks[chunk_id]

            # 获取当前章节信息 (parse_txt 返回的是 List[Tuple[str, int]]，即 [(title, start_chunk), ...])
            chapter_title = "未知章节"
            chapter_start = 0
            for i, chapter in enumerate(chapters):
                # chapter 是 tuple: (title, start_chunk)
                c_title = chapter[0]
                c_start = chapter[1]
                if i + 1 < len(chapters):
                    next_chapter_start = chapters[i + 1][1]
                    if c_start <= chunk_id < next_chapter_start:
                        chapter_title = c_title
                        chapter_start = c_start
                        break
                else:
                    if c_start <= chunk_id:
                        chapter_title = c_title
                        chapter_start = c_start
                        break

            # 计算在章节中的位置
            position_in_chapter = chunk_id - chapter_start

            # 构建显示文本
            display_text = f"《{book['title']}》\n\n"
            display_text += f"【{chapter_title}】\n"
            display_text += f"Chunk {chunk_id} (章节内第 {position_in_chapter + 1} 段)\n"
            display_text += f"{'─' * 40}\n\n"
            display_text += current_chunk_text

            self.text_display.setPlainText(display_text)

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
