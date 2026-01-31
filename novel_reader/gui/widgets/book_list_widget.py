"""
书籍列表组件 - 显示书籍列表，支持拖拽导入文件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QFileDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal, QUrl, QPoint
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from typing import Optional
from pathlib import Path


class BookListWidget(QWidget):
    """书籍列表组件，支持拖拽导入"""

    # 信号定义
    book_selected = Signal(int)  # 书籍被选中，参数：book_id
    book_double_clicked = Signal(int)  # 书籍被双击，参数：book_id
    books_updated = Signal()  # 书籍列表更新
    book_delete_requested = Signal(int)  # 请求删除书籍，参数：book_id
    book_rename_requested = Signal(int, str)  # 请求重命名书籍，参数：book_id, current_title
    book_imported = Signal(int)  # 书籍导入成功，参数：book_id

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None

        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("📚 书籍列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 书籍树形列表
        self.books_tree = QTreeWidget()
        self.books_tree.setHeaderLabels(["ID", "书名", "进度", "最后播放"])
        self.books_tree.setColumnWidth(0, 50)
        self.books_tree.setColumnWidth(1, 200)
        self.books_tree.setColumnWidth(2, 100)
        self.books_tree.setColumnWidth(3, 150)
        self.books_tree.setAlternatingRowColors(True)
        self.books_tree.setRootIsDecorated(False)
        self.books_tree.setContextMenuPolicy(Qt.CustomContextMenu)

        # 连接信号
        self.books_tree.itemClicked.connect(self._on_item_clicked)
        self.books_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.books_tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.books_tree)

    def _setup_drag_drop(self):
        """设置拖拽支持"""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否是文件
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()

        imported_count = 0
        failed_files = []

        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()

                # 只处理 .txt 文件
                if Path(file_path).suffix.lower() != '.txt':
                    failed_files.append((file_path, "不是 TXT 文件"))
                    continue

                try:
                    from novel_reader.core import import_book
                    import_book(file_path)
                    imported_count += 1
                except Exception as e:
                    failed_files.append((file_path, str(e)))

        # 显示导入结果
        if imported_count > 0:
            self.load_books()
            QMessageBox.information(
                self,
                "导入成功",
                f"成功导入 {imported_count} 本书"
            )

            # 为每本导入的书籍发射信号（触发自动转换前2个chunk）
            from novel_reader.core import list_books
            books = list_books()
            # 获取最新导入的书籍（最后导入的几本）
            for book in books[:imported_count]:
                self.book_imported.emit(book['id'])

        if failed_files:
            error_msg = "以下文件导入失败:\n\n"
            for file_path, reason in failed_files:
                error_msg += f"{Path(file_path).name}: {reason}\n"
            QMessageBox.warning(self, "导入失败", error_msg)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """项目点击事件"""
        book_id_text = item.text(0)

        if book_id_text == "-":
            return

        self.current_book_id = int(book_id_text)
        self.book_selected.emit(self.current_book_id)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """项目双击事件"""
        book_id_text = item.text(0)

        if book_id_text == "-":
            return

        book_id = int(book_id_text)
        self.book_double_clicked.emit(book_id)

    def _show_context_menu(self, pos: QPoint):
        """显示右键菜单"""
        item = self.books_tree.itemAt(pos)

        if not item:
            return

        book_id_text = item.text(0)

        if book_id_text == "-":
            return

        book_id = int(book_id_text)

        # 创建右键菜单
        menu = QMenu(self)

        # 重命名操作
        rename_action = menu.addAction("✏️ 重命名")

        # 删除操作
        delete_action = menu.addAction("🗑️ 删除书籍")

        # 显示菜单并获取用户选择
        action = menu.exec_(self.books_tree.mapToGlobal(pos))

        if action == rename_action:
            # 获取当前书名
            from novel_reader.core import get_book
            book = get_book(book_id)
            if book:
                self.book_rename_requested.emit(book_id, book['title'])

        elif action == delete_action:
            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除这本书吗？\n\n"
                "这将同时删除：\n"
                "• 书籍信息\n"
                "• 章节信息\n"
                "• 书签记录\n"
                "• 已转换的音频文件",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.book_delete_requested.emit(book_id)

    def load_books(self, auto_select_book_id: int = None):
        """
        加载书籍列表

        Args:
            auto_select_book_id: 自动选中的书籍ID（可选）
        """
        from novel_reader.core import list_books, get_book_chapters
        from novel_reader.models import get_conn
        from datetime import datetime

        self.books_tree.clear()

        books = list_books()

        if not books:
            item = QTreeWidgetItem(["-", "暂无书籍", "-", "-"])
            item.setTextAlignment(0, Qt.AlignCenter)
            item.setTextAlignment(1, Qt.AlignCenter)
            item.setTextAlignment(2, Qt.AlignCenter)
            item.setTextAlignment(3, Qt.AlignCenter)
            self.books_tree.addTopLevelItem(item)
            return

        for book in books:
            # 获取章节数
            chapters = get_book_chapters(book['id'])
            total_chapters = len(chapters)

            # 格式化进度信息
            current_chapter = book.get('current_chapter', 0)
            current_chunk = book.get('current_chunk', 0)

            if total_chapters > 0:
                if current_chapter >> 0:
                    progress_text = f"第{current_chapter}章"
                else:
                    progress_text = "无"
            else:
                progress_text = f"{current_chunk}"

            # 格式化最后播放时间
            last_played_at = book.get('last_played_at')
            if last_played_at:
                try:
                    dt = datetime.fromisoformat(last_played_at)
                    # 计算相对时间
                    now = datetime.now()
                    diff = now - dt
                    if diff.days > 0:
                        time_text = f"{diff.days}天前"
                    elif diff.seconds >= 3600:
                        hours = diff.seconds // 3600
                        time_text = f"{hours}小时前"
                    elif diff.seconds >= 60:
                        minutes = diff.seconds // 60
                        time_text = f"{minutes}分钟前"
                    else:
                        time_text = "刚刚"
                except:
                    time_text = last_played_at[:10] if len(last_played_at) > 10 else last_played_at
            else:
                time_text = "未播放"

            item = QTreeWidgetItem([
                str(book['id']),
                book['title'],
                progress_text,
                time_text
            ])
            self.books_tree.addTopLevelItem(item)

        # 自动选中指定的书籍（或第一本书）
        if books and self.books_tree.selectedItems():
            pass  # 已有选中，不需要操作
        elif books:
            # 查找要自动选中的书
            item_to_select = None

            if auto_select_book_id is not None:
                # 查找指定ID的书
                for i in range(self.books_tree.topLevelItemCount()):
                    item = self.books_tree.topLevelItem(i)
                    book_id = int(item.text(0))
                    if book_id == auto_select_book_id:
                        item_to_select = item
                        break

            # 如果没找到指定ID的书，默认选中第一本
            if item_to_select is None:
                item_to_select = self.books_tree.topLevelItem(0)

            self.books_tree.setCurrentItem(item_to_select)
            # 触发选中事件
            book_id = int(item_to_select.text(0))
            self.current_book_id = book_id
            self.book_selected.emit(book_id)
            print(f"[INFO] Auto-selected book: {book_id}")

        self.books_updated.emit()

    def select_book_by_id(self, book_id: int) -> bool:
        """
        通过ID选中书籍

        Args:
            book_id: 书籍ID

        Returns:
            是否成功选中
        """
        for i in range(self.books_tree.topLevelItemCount()):
            item = self.books_tree.topLevelItem(i)
            if item.text(0) == "-":
                continue

            item_book_id = int(item.text(0))
            if item_book_id == book_id:
                self.books_tree.setCurrentItem(item)
                self.current_book_id = book_id
                self.book_selected.emit(book_id)
                print(f"[INFO] Selected book: {book_id}")
                return True

        return False

    def get_selected_book_id(self) -> Optional[int]:
        """获取当前选中的书籍 ID"""
        selected_items = self.books_tree.selectedItems()

        if not selected_items:
            return None

        item = selected_items[0]
        book_id_text = item.text(0)

        if book_id_text == "-":
            return None

        return int(book_id_text)

    def import_book_dialog(self):
        """打开导入书籍对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要导入的 TXT 文件",
            "",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                from novel_reader.core import import_book
                book_id = import_book(file_path)
                QMessageBox.information(
                    self,
                    "成功",
                    f"导入成功！书籍 ID: {book_id}"
                )
                self.load_books()

                # 发射导入成功信号
                self.book_imported.emit(book_id)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")
