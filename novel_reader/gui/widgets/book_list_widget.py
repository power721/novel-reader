"""
书籍列表组件 - 显示书籍列表，支持拖拽导入文件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QFileDialog, QMessageBox, QMenu, QDialog,
    QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor
from typing import Optional
from pathlib import Path
import os


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
        self.playing_book_id: Optional[int] = None  # 正在播放的书籍ID

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
        self.books_tree.setColumnWidth(0, 30)
        self.books_tree.setColumnWidth(1, 250)
        self.books_tree.setColumnWidth(2, 100)
        self.books_tree.setColumnWidth(3, 100)
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

                # 支持电子书格式
                from novel_reader.utils.ebook_converter import is_ebook_file

                file_suffix = Path(file_path).suffix.lower()
                if file_suffix != '.txt' and not is_ebook_file(file_path):
                    failed_files.append((file_path, "不支持的文件格式"))
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

        # 书籍信息操作
        info_action = menu.addAction("ℹ️ 书籍信息")

        # 添加分隔线
        menu.addSeparator()

        # 文件操作
        open_book_file_action = menu.addAction("📄 打开书籍文件")
        open_book_dir_action = menu.addAction("📂 打开书籍目录")

        # 添加分隔线
        menu.addSeparator()

        # 音频文件操作
        open_audio_dir_action = menu.addAction("📁 打开音频目录")
        check_audio_size_action = menu.addAction("📊 查看音频大小")
        clean_audio_cache_action = menu.addAction("🧹 清理音频缓存")

        # 添加分隔线
        menu.addSeparator()

        # 重命名操作
        rename_action = menu.addAction("✏️ 重命名")

        # 删除操作
        delete_action = menu.addAction("🗑️ 删除书籍")

        # 显示菜单并获取用户选择
        action = menu.exec_(self.books_tree.mapToGlobal(pos))

        if action == info_action:
            self._show_book_info(book_id)

        elif action == open_book_file_action:
            self._open_book_file(book_id)

        elif action == open_book_dir_action:
            self._open_book_directory(book_id)

        elif action == open_audio_dir_action:
            self._open_audio_directory(book_id)

        elif action == check_audio_size_action:
            self._check_audio_size(book_id)

        elif action == clean_audio_cache_action:
            self._clean_audio_cache(book_id)

        elif action == rename_action:
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
                progress_text = f"{current_chapter}/{total_chapters}章"
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

        # 应用正在播放的高亮（必须在所有item添加完成后）
        self._apply_playing_highlight()

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
            "选择要导入的书籍",
            "",
            "支持的格式 (*.txt *.epub *.mobi *.azw3 *.azw);;文本文件 (*.txt);;电子书 (*.epub *.mobi *.azw3 *.azw);;所有文件 (*)"
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

    def _show_book_info(self, book_id: int):
        """显示书籍信息对话框"""
        from novel_reader.core import get_book, get_book_chapters

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        chapters = get_book_chapters(book_id)

        # 获取文件大小
        file_size = "未知"
        if book['file_path'] and os.path.exists(book['file_path']):
            try:
                size_bytes = os.path.getsize(book['file_path'])
                # 格式化为人类可读的大小
                if size_bytes < 1024:
                    file_size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    file_size = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    file_size = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            except Exception as e:
                file_size = f"获取失败: {e}"

        # 获取文本文件统计信息
        char_count = "-"
        chunk_count = "-"
        if book['file_path'] and os.path.exists(book['file_path']):
            try:
                with open(book['file_path'], 'r', encoding='utf-8') as f:
                    text = f.read()
                    char_count = f"{len(text):,}"
            except Exception as e:
                char_count = f"读取失败: {e}"

        # 使用数据库中保存的 chunk 数量
        if book.get('chunk_count') and book['chunk_count'] > 0:
            chunk_count = f"{book['chunk_count']:,}"

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"书籍信息 - {book['title']}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)

        # 书籍基本信息
        layout.addRow("书名：", QLabel(book['title']))
        layout.addRow("书籍 ID：", QLabel(str(book['id'])))

        # 文件信息
        file_path_label = QLabel(book['file_path'] or "未知")
        file_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        file_path_label.setWordWrap(True)
        layout.addRow("文件路径：", file_path_label)

        layout.addRow("文件大小：", QLabel(file_size))
        layout.addRow("字符数：", QLabel(char_count))
        layout.addRow("分段数量：", QLabel(chunk_count))

        # 原始文件信息
        if book['original_filename']:
            layout.addRow("原始文件名：", QLabel(book['original_filename']))
        if book['file_format']:
            layout.addRow("文件格式：", QLabel(book['file_format'].upper()))

        # 章节信息
        layout.addRow("章节数量：", QLabel(str(len(chapters))))

        # 播放进度
        current_chapter = book.get('current_chapter', 0)
        current_chunk = book.get('current_chunk', 0)
        layout.addRow("当前章节：", QLabel(str(current_chapter)))
        layout.addRow("当前分段：", QLabel(str(current_chunk)))

        # 时间信息
        created_at = book.get('created_at', '')
        if created_at:
            created_label = QLabel(created_at[:19].replace('T', ' '))
            layout.addRow("导入时间：", created_label)

        updated_at = book.get('updated_at', '')
        if updated_at:
            updated_label = QLabel(updated_at[:19].replace('T', ' '))
            layout.addRow("更新时间：", updated_label)

        last_played_at = book.get('last_played_at')
        if last_played_at:
            last_played_label = QLabel(last_played_at[:19].replace('T', ' '))
            layout.addRow("最后播放：", last_played_label)

        # 添加确定按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addRow(buttons)

        dialog.exec()

    def set_playing_book(self, book_id: Optional[int]):
        """
        设置正在播放的书籍并高亮显示

        Args:
            book_id: 正在播放的书籍ID，如果为None则清除高亮
        """
        old_playing_id = self.playing_book_id
        self.playing_book_id = book_id

        # 如果书籍ID发生变化，重新加载列表以更新高亮
        if old_playing_id != book_id:
            # 使用正在播放的书籍ID来保持选中状态
            select_id = book_id if book_id is not None else self.current_book_id
            self.load_books(auto_select_book_id=select_id)

    def _apply_playing_highlight(self):
        """应用正在播放的高亮样式"""
        if self.playing_book_id is None:
            # 清除所有高亮
            for i in range(self.books_tree.topLevelItemCount()):
                item = self.books_tree.topLevelItem(i)
                if item.text(0) != "-":
                    # 清除自定义样式
                    for col in range(item.columnCount()):
                        item.setData(col, Qt.BackgroundRole, None)
                        item.setData(col, Qt.ForegroundRole, None)
                    # 移除播放图标
                    title = item.text(1)
                    if title.startswith("▶ "):
                        item.setText(1, title[2:])
        else:
            # 应用高亮到正在播放的书籍
            for i in range(self.books_tree.topLevelItemCount()):
                item = self.books_tree.topLevelItem(i)
                if item.text(0) == "-":
                    continue

                book_id = int(item.text(0))
                if book_id == self.playing_book_id:
                    # 设置高亮样式
                    for col in range(item.columnCount()):
                        item.setBackground(col, QColor("#e8f5e9"))
                        if col == 1:  # 书名列使用深绿色文字
                            item.setForeground(col, QColor("#1b5e20"))
                    # 添加播放图标
                    title = item.text(1)
                    if not title.startswith("▶️ "):
                        item.setText(1, f"▶️ {title}")
                else:
                    # 清除其他书籍的高亮
                    for col in range(item.columnCount()):
                        item.setData(col, Qt.BackgroundRole, None)
                        item.setData(col, Qt.ForegroundRole, None)
                    # 移除播放图标
                    title = item.text(1)
                    if title.startswith("▶️ "):
                        item.setText(1, title[2:].strip())

    def _open_book_directory(self, book_id: int):
        """打开书籍的原始文件目录"""
        from novel_reader.core import get_book
        import subprocess
        import os

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        # 获取文件路径
        file_path = book.get('file_path')
        if not file_path:
            QMessageBox.warning(self, "文件路径", "该书籍没有文件路径信息")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "文件不存在",
                f"原始文件不存在：\n\n{file_path}"
            )
            return

        # 获取文件所在目录
        book_dir = os.path.dirname(file_path)
        abs_dir = os.path.abspath(book_dir)

        try:
            # 使用文件管理器打开目录
            subprocess.run(['xdg-open', abs_dir], check=False)
            print(f"[INFO] Opened book directory: {abs_dir}")
        except FileNotFoundError:
            try:
                # Fallback 到 nautilus (GNOME) - 直接选中文件
                abs_path = os.path.abspath(file_path)
                subprocess.run(['nautilus', '--select', abs_path], check=False)
            except FileNotFoundError:
                try:
                    # Fallback 到 dolphin (KDE) - 直接选中文件
                    subprocess.run(['dolphin', '--select', abs_path], check=False)
                except FileNotFoundError:
                    # 最后的 fallback - 只打开目录
                    abs_dir = os.path.abspath(book_dir)
                    os.system(f'xdg-open "{abs_dir}"')

    def _open_book_file(self, book_id: int):
        """打开书籍的原始文件"""
        from novel_reader.core import get_book
        import subprocess
        import os

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        # 获取文件路径
        file_path = book.get('file_path')
        if not file_path:
            QMessageBox.warning(self, "文件路径", "该书籍没有文件路径信息")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "文件不存在",
                f"原始文件不存在：\n\n{file_path}"
            )
            return

        try:
            # 使用文件管理器打开目录并选中文件
            subprocess.run(['xdg-open', file_path], check=False)
            abs_path = os.path.abspath(file_path)
            print(f"[INFO] Opened book file: {abs_path}")
        except FileNotFoundError:
            try:
                # Fallback 到 nautilus (GNOME) - 直接选中文件
                abs_path = os.path.abspath(file_path)
                subprocess.run(['nautilus', '--select', abs_path], check=False)
            except FileNotFoundError:
                try:
                    # Fallback 到 dolphin (KDE) - 直接选中文件
                    subprocess.run(['dolphin', '--select', abs_path], check=False)
                except FileNotFoundError:
                    # 最后的 fallback - 只打开目录
                    book_dir = os.path.dirname(file_path)
                    abs_dir = os.path.abspath(book_dir)
                    os.system(f'xdg-open "{abs_dir}"')

    def _open_audio_directory(self, book_id: int):
        """打开书籍的音频目录"""
        from novel_reader.core import get_book
        import subprocess
        import os

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        # 构建音频目录路径（使用项目的 data/audio 目录）
        audio_dir = f"data/audio/{book_id}"

        if not os.path.exists(audio_dir):
            QMessageBox.information(
                self,
                "音频目录",
                f"该书还没有生成音频文件\n\n音频目录：{audio_dir}"
            )
            return

        try:
            # 转换为绝对路径
            abs_audio_dir = os.path.abspath(audio_dir)

            # 使用文件管理器打开目录
            subprocess.run(['xdg-open', abs_audio_dir], check=False)
            print(f"[INFO] Opened audio directory: {abs_audio_dir}")
        except FileNotFoundError:
            try:
                # Fallback 到 nautilus (GNOME)
                subprocess.run(['nautilus', abs_audio_dir], check=False)
            except FileNotFoundError:
                try:
                    # Fallback 到 dolphin (KDE)
                    subprocess.run(['dolphin', abs_audio_dir], check=False)
                except FileNotFoundError:
                    # 最后的 fallback - 直接用 xdg-open
                    os.system(f'xdg-open "{abs_audio_dir}"')

    def _check_audio_size(self, book_id: int):
        """查看书籍的音频文件大小"""
        from novel_reader.core import get_book
        import os

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        # 构建音频目录路径（使用项目的 data/audio 目录）
        audio_dir = f"data/audio/{book_id}"

        if not os.path.exists(audio_dir):
            QMessageBox.information(
                self,
                "音频文件",
                f"该书还没有生成音频文件\n\n书籍：{book['title']}"
            )
            return

        # 统计音频文件
        total_size = 0
        file_count = 0
        from pathlib import Path

        audio_path = Path(audio_dir)
        for audio_file in audio_path.rglob("*"):
            if audio_file.suffix.lower() in {".wav", ".mp3"}:
                total_size += audio_file.stat().st_size
                file_count += 1

        # 格式化大小
        if total_size < 1024:
            size_text = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_text = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_text = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_text = f"{total_size / (1024 * 1024 * 1024):.2f} GB"

        # 显示信息
        abs_audio_dir = os.path.abspath(audio_dir)
        QMessageBox.information(
            self,
            "音频文件统计",
            f"书籍：{book['title']}\n\n"
            f"音频文件数量：{file_count}\n"
            f"总大小：{size_text}\n\n"
            f"音频目录：\n{abs_audio_dir}"
        )

    def _clean_audio_cache(self, book_id: int):
        """清理书籍的音频缓存"""
        from novel_reader.core import get_book
        import os
        import shutil

        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "无法获取书籍信息")
            return

        # 构建音频目录路径（使用项目的 data/audio 目录）
        audio_dir = f"data/audio/{book_id}"

        if not os.path.exists(audio_dir):
            QMessageBox.information(
                self,
                "音频缓存",
                f"该书还没有音频缓存\n\n书籍：{book['title']}"
            )
            return

        # 确认清理
        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定要清理「{book['title']}」的音频缓存吗？\n\n"
            f"这将删除所有已生成的音频文件，但不会删除书籍信息。\n\n"
            f"下次播放时需要重新转换音频。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 统计文件数量
            from pathlib import Path
            file_count = 0
            audio_path = Path(audio_dir)
            for audio_file in audio_path.rglob("*"):
                if audio_file.suffix.lower() in {".wav", ".mp3"}:
                    file_count += 1

            # 删除音频目录
            shutil.rmtree(audio_dir)
            abs_audio_dir = os.path.abspath(audio_dir)
            print(f"[INFO] Cleaned audio cache for book {book_id}: {abs_audio_dir}")

            QMessageBox.information(
                self,
                "清理成功",
                f"已清理「{book['title']}」的音频缓存\n\n"
                f"共删除 {file_count} 个音频文件\n"
                f"目录：{abs_audio_dir}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "清理失败",
                f"清理音频缓存时出错：\n{str(e)}"
            )
