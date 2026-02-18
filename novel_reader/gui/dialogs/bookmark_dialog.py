"""
书签对话框 - 显示和管理书签
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QMenu,
    QLineEdit, QMessageBox, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List, Dict
from datetime import datetime


class BookmarkDialog(QDialog):
    """书签管理对话框"""

    # 信号：用户选择跳转到某个书签
    jump_to_bookmark = Signal(int)  # 参数：chunk 索引

    def __init__(self, book_id: int, book_title: str, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self.book_title = book_title
        self.bookmarks: List[Dict] = []
        self._setup_ui()
        self._load_bookmarks()

    def _setup_ui(self):
        """设置界面"""
        self.setWindowTitle(f"🔖 书签 - {self.book_title}")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题区域
        title_layout = QHBoxLayout()

        title_label = QLabel(f"📖 {self.book_title}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529;")
        title_layout.addWidget(title_label)

        layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 书签列表
        list_label = QLabel("书签列表:")
        list_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057;")
        layout.addWidget(list_label)

        self.bookmark_list = QListWidget()
        self.bookmark_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 5px;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        self.bookmark_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_list.customContextMenuRequested.connect(self._show_context_menu)
        self.bookmark_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.bookmark_list)

        # 底部按钮
        button_layout = QHBoxLayout()

        self.add_note_btn = QPushButton("📝 添加备注")
        self.add_note_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.add_note_btn.clicked.connect(self._add_note_to_selected)
        self.add_note_btn.setEnabled(False)
        button_layout.addWidget(self.add_note_btn)

        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # 连接选择变化信号
        self.bookmark_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_bookmarks(self):
        """加载书签列表"""
        from novel_reader.core.book import get_bookmarks

        self.bookmarks = get_bookmarks(self.book_id)
        self.bookmark_list.clear()

        if not self.bookmarks:
            # 显示空状态提示
            empty_item = QListWidgetItem()
            empty_item.setText("📭 暂无书签\n\n在音频播放时按 Ctrl+B 添加书签")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选中
            self.bookmark_list.addItem(empty_item)
            return

        for bookmark in self.bookmarks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, bookmark)

            # 格式化时间
            created_time = datetime.fromisoformat(bookmark['created_at'])
            time_str = created_time.strftime("%Y-%m-%d %H:%M")

            # 构建显示文本（包含章节信息）
            chapter_text = f" · {bookmark['chapter_title']}" if bookmark.get('chapter_title') else ""
            note_text = f"\n📝 {bookmark['note']}" if bookmark['note'] else ""
            text = f"🔖 第{bookmark['chunk']}段{chapter_text}{note_text}\n🕐 {time_str}"

            item.setText(text)
            self.bookmark_list.addItem(item)

    def _on_selection_changed(self):
        """选择变化时更新按钮状态"""
        has_selection = len(self.bookmark_list.selectedItems()) > 0
        self.add_note_btn.setEnabled(has_selection)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.bookmark_list.itemAt(pos)
        if not item:
            return

        bookmark = item.data(Qt.UserRole)
        if not bookmark:
            return

        menu = QMenu(self)

        # 跳转书签
        jump_action = menu.addAction("🚀 跳转到此处")
        jump_action.triggered.connect(lambda: self._jump_to_bookmark(bookmark))

        # 添加备注
        note_action = menu.addAction("📝 编辑备注")
        note_action.triggered.connect(lambda: self._edit_note(bookmark))

        menu.addSeparator()

        # 删除书签
        delete_action = menu.addAction("🗑️ 删除书签")
        delete_action.triggered.connect(lambda: self._delete_bookmark(bookmark['id']))

        menu.exec_(self.bookmark_list.mapToGlobal(pos))

    def _on_item_double_clicked(self, item):
        """双击项目时跳转"""
        bookmark = item.data(Qt.UserRole)
        if bookmark:
            self._jump_to_bookmark(bookmark)

    def _jump_to_bookmark(self, bookmark: Dict):
        """跳转到书签位置"""
        self.jump_to_bookmark.emit(bookmark['chunk'])
        self.accept()
        QMessageBox.information(
            self,
            "跳转成功",
            f"已跳转到分段 {bookmark['chunk']}",
            QMessageBox.Ok
        )

    def _add_note_to_selected(self):
        """为选中的书签添加备注"""
        selected_items = self.bookmark_list.selectedItems()
        if not selected_items:
            return

        bookmark = selected_items[0].data(Qt.UserRole)
        if bookmark:
            self._edit_note(bookmark)

    def _edit_note(self, bookmark: Dict):
        """编辑书签备注"""
        from PySide6.QtWidgets import QInputDialog

        new_note, ok = QInputDialog.getText(
            self,
            "编辑备注",
            "请输入书签备注:",
            text=bookmark['note']
        )

        if ok:
            from novel_reader.core.book import remove_bookmark, add_bookmark

            # 删除旧书签，添加新书签（更新备注）
            old_id = bookmark['id']
            chunk = bookmark['chunk']

            remove_bookmark(old_id)
            add_bookmark(self.book_id, chunk, new_note)

            # 重新加载列表
            self._load_bookmarks()

    def _delete_bookmark(self, bookmark_id: int):
        """删除书签"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个书签吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from novel_reader.core.book import remove_bookmark

            if remove_bookmark(bookmark_id):
                self._load_bookmarks()
                QMessageBox.information(
                    self,
                    "删除成功",
                    "书签已删除",
                    QMessageBox.Ok
                )


class AllBookmarksDialog(QDialog):
    """所有书签对话框"""

    # 信号：用户选择跳转到某个书签
    jump_to_bookmark = Signal(int, int)  # 参数：book_id, chunk 索引

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bookmarks: List[Dict] = []
        self._setup_ui()
        self._load_bookmarks()

    def _setup_ui(self):
        """设置界面"""
        self.setWindowTitle("🔖 所有书签")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("📚 所有书签")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 书签列表
        self.bookmark_list = QListWidget()
        self.bookmark_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin-bottom: 5px;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        self.bookmark_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_list.customContextMenuRequested.connect(self._show_context_menu)
        self.bookmark_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.bookmark_list)

        # 底部按钮
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        refresh_btn.clicked.connect(self._load_bookmarks)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _load_bookmarks(self):
        """加载所有书签"""
        from novel_reader.core.book import get_all_bookmarks

        self.bookmarks = get_all_bookmarks()
        self.bookmark_list.clear()

        if not self.bookmarks:
            # 显示空状态提示
            empty_item = QListWidgetItem()
            empty_item.setText("📭 暂无书签\n\n在音频播放时按 Ctrl+B 添加书签")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选中
            self.bookmark_list.addItem(empty_item)
            return

        for bookmark in self.bookmarks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, bookmark)

            # 格式化时间
            created_time = datetime.fromisoformat(bookmark['created_at'])
            time_str = created_time.strftime("%Y-%m-%d %H:%M")

            # 构建显示文本（包含章节信息）
            chapter_text = f" · {bookmark['chapter_title']}" if bookmark.get('chapter_title') else ""
            note_text = f"\n📝 {bookmark['note']}" if bookmark['note'] else ""
            text = f"📖 {bookmark['book_title']}\n🔖 第{bookmark['chunk']}段{chapter_text}{note_text}\n🕐 {time_str}"

            item.setText(text)
            self.bookmark_list.addItem(item)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.bookmark_list.itemAt(pos)
        if not item:
            return

        bookmark = item.data(Qt.UserRole)
        if not bookmark:
            return

        menu = QMenu(self)

        # 跳转书签
        jump_action = menu.addAction("🚀 跳转到此处")
        jump_action.triggered.connect(lambda: self._jump_to_bookmark(bookmark))

        menu.addSeparator()

        # 删除书签
        delete_action = menu.addAction("🗑️ 删除书签")
        delete_action.triggered.connect(lambda: self._delete_bookmark(bookmark['id']))

        menu.exec_(self.bookmark_list.mapToGlobal(pos))

    def _on_item_double_clicked(self, item):
        """双击项目时跳转"""
        bookmark = item.data(Qt.UserRole)
        if bookmark:
            self._jump_to_bookmark(bookmark)

    def _jump_to_bookmark(self, bookmark: Dict):
        """跳转到书签位置"""
        self.jump_to_bookmark.emit(bookmark['book_id'], bookmark['chunk'])

        # 如果不是当前书籍，需要先切换书籍
        if self.parent() and hasattr(self.parent(), 'current_book_id'):
            if self.parent().current_book_id != bookmark['book_id']:
                # 切换书籍并跳转
                if hasattr(self.parent(), '_jump_to_bookmark_in_book'):
                    self.parent()._jump_to_bookmark_in_book(bookmark['book_id'], bookmark['chunk'])
                    self.accept()
                    QMessageBox.information(
                        self,
                        "跳转成功",
                        f"已切换到《{bookmark['book_title']}》并跳转到分段 {bookmark['chunk']}",
                        QMessageBox.Ok
                    )
            else:
                # 当前书籍，直接跳转
                from novel_reader.core.book import get_book

                book = get_book(bookmark['book_id'])
                if book and hasattr(self.parent(), '_play_from_chunk'):
                    self.parent()._play_from_chunk(bookmark['chunk'])
                    self.accept()
                    QMessageBox.information(
                        self,
                        "跳转成功",
                        f"已跳转到分段 {bookmark['chunk']}",
                        QMessageBox.Ok
                    )

    def _delete_bookmark(self, bookmark_id: int):
        """删除书签"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个书签吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from novel_reader.core.book import remove_bookmark

            if remove_bookmark(bookmark_id):
                self._load_bookmarks()
                QMessageBox.information(
                    self,
                    "删除成功",
                    "书签已删除",
                    QMessageBox.Ok
                )
