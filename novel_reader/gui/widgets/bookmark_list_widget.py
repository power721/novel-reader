"""
书签列表组件 - 显示和管理书签
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from typing import Optional


class BookmarkListWidget(QWidget):
    """书签列表组件"""

    # 信号定义
    bookmark_double_clicked = Signal(int)  # 书签被双击，参数：chunk

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("🔖 书签列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 书签树形列表
        self.bookmarks_tree = QTreeWidget()
        self.bookmarks_tree.setHeaderLabels(["ID", "位置", "笔记"])
        self.bookmarks_tree.setColumnWidth(0, 60)
        self.bookmarks_tree.setColumnWidth(1, 100)
        self.bookmarks_tree.setColumnWidth(2, 250)
        self.bookmarks_tree.setAlternatingRowColors(True)
        self.bookmarks_tree.setRootIsDecorated(False)

        # 连接信号
        self.bookmarks_tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.bookmarks_tree)

        # 按钮栏
        btn_layout = QHBoxLayout()

        self.add_bookmark_btn = QPushButton("添加书签")
        self.add_bookmark_btn.clicked.connect(self.add_bookmark)

        self.add_note_btn = QPushButton("添加笔记")
        self.add_note_btn.clicked.connect(self.add_note)

        self.delete_bookmark_btn = QPushButton("删除书签")
        self.delete_bookmark_btn.clicked.connect(self.delete_bookmark)

        btn_layout.addWidget(self.add_bookmark_btn)
        btn_layout.addWidget(self.add_note_btn)
        btn_layout.addWidget(self.delete_bookmark_btn)

        layout.addLayout(btn_layout)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """项目双击事件"""
        chunk_text = item.text(1)

        if chunk_text == "-" or not chunk_text:
            return

        chunk = int(chunk_text)
        self.bookmark_double_clicked.emit(chunk)

    def load_bookmarks(self, book_id: int):
        """加载书签列表"""
        from novel_reader.core import get_bookmarks

        self.current_book_id = book_id
        self.bookmarks_tree.clear()

        if book_id is None:
            item = QTreeWidgetItem(["-", "-", "请先选择书籍"])
            item.setTextAlignment(0, Qt.AlignCenter)
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setTextAlignment(2, Qt.AlignCenter)
            self.bookmarks_tree.addTopLevelItem(item)
            return

        bookmarks = get_bookmarks(book_id)

        if not bookmarks:
            item = QTreeWidgetItem(["-", "-", "暂无书签"])
            item.setTextAlignment(0, Qt.AlignCenter)
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setTextAlignment(2, Qt.AlignCenter)
            self.bookmarks_tree.addTopLevelItem(item)
            return

        for bm in bookmarks:
            note = bm['note'] if bm['note'] else ""
            note_text = note[:30] + "..." if len(note) > 30 else note
            item = QTreeWidgetItem([
                str(bm['id']),
                str(bm['chunk']),
                note_text
            ])
            self.bookmarks_tree.addTopLevelItem(item)

    def add_bookmark(self):
        """添加书签"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book, add_bookmark

        book = get_book(self.current_book_id)
        if book is None:
            QMessageBox.critical(self, "错误", "书籍不存在")
            return

        current_chunk = book['current_chunk']
        add_bookmark(self.current_book_id, current_chunk, f"Chunk {current_chunk}")

        QMessageBox.information(self, "成功", f"已添加书签: Chunk {current_chunk}")
        self.load_bookmarks(self.current_book_id)

    def add_note(self):
        """添加带笔记的书签"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book, add_bookmark

        book = get_book(self.current_book_id)
        if book is None:
            QMessageBox.critical(self, "错误", "书籍不存在")
            return

        current_chunk = book['current_chunk']

        # 输入对话框
        note, ok = QInputDialog.getText(
            self,
            "添加书签笔记",
            "请输入笔记内容:",
            text=f"Chunk {current_chunk}"
        )

        if ok and note:
            add_bookmark(self.current_book_id, current_chunk, note)
            QMessageBox.information(self, "成功", f"已添加书签: Chunk {current_chunk}")
            self.load_bookmarks(self.current_book_id)

    def delete_bookmark(self):
        """删除书签"""
        selected_items = self.bookmarks_tree.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个书签")
            return

        item = selected_items[0]
        bookmark_id_text = item.text(0)

        if bookmark_id_text == "-":
            return

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除选中的书签吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            bookmark_id = int(bookmark_id_text)

            from novel_reader.core import delete_bookmark
            delete_bookmark(bookmark_id)

            QMessageBox.information(self, "成功", "已删除书签")
            self.load_bookmarks(self.current_book_id)

    def clear(self):
        """清空列表"""
        self.bookmarks_tree.clear()
        self.current_book_id = None
