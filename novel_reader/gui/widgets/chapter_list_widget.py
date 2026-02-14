"""
章节列表组件 - 显示书籍的章节列表
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QMenu
)
from PySide6.QtCore import Qt, Signal, QPoint
from typing import Optional


class ChapterListWidget(QWidget):
    """章节列表组件"""

    # 信号定义
    chapter_selected = Signal(int)  # 章节被选中，参数：start_chunk
    chapter_double_clicked = Signal(int)  # 章节被双击，参数：start_chunk
    convert_chapter_requested = Signal(int, int)  # 请求转换章节，参数：start_chunk, end_chunk

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.chapters: list = []  # 保存章节数据

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel("📖 章节列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # 章节树形列表
        self.chapters_tree = QTreeWidget()
        self.chapters_tree.setHeaderLabels(["章节标题", "分段"])
        self.chapters_tree.setColumnWidth(0, 350)
        self.chapters_tree.setColumnWidth(1, 30)
        self.chapters_tree.setAlternatingRowColors(True)
        self.chapters_tree.setRootIsDecorated(False)
        self.chapters_tree.setContextMenuPolicy(Qt.CustomContextMenu)

        # 启用高亮样式
        self.chapters_tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 5px;
            }
        """)

        # 连接信号
        self.chapters_tree.itemClicked.connect(self._on_item_clicked)
        self.chapters_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.chapters_tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.chapters_tree)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """项目点击事件"""
        # 从第0列获取存储的 start_chunk
        start_chunk = item.data(0, Qt.UserRole)

        if start_chunk is None:
            return

        self.chapter_selected.emit(start_chunk)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """项目双击事件"""
        # 从第0列获取存储的 start_chunk
        start_chunk = item.data(0, Qt.UserRole)

        if start_chunk is None:
            return

        self.chapter_double_clicked.emit(start_chunk)

    def _show_context_menu(self, pos: QPoint):
        """显示右键菜单"""
        item = self.chapters_tree.itemAt(pos)
        if not item:
            return

        start_chunk = item.data(0, Qt.UserRole)
        if start_chunk is None:
            return

        # 找到对应的章节数据
        chapter_data = None
        for chapter in self.chapters:
            if chapter['start_chunk'] == start_chunk:
                chapter_data = chapter
                break

        if not chapter_data:
            return

        # 创建右键菜单
        menu = QMenu(self)

        convert_action = menu.addAction("🔄 转换本章节 TTS")
        convert_action.setToolTip(f"转换《{chapter_data['title']}》的所有 {chapter_data['chunk_count']} 个分段")

        # 显示菜单并获取用户选择
        action = menu.exec_(self.chapters_tree.mapToGlobal(pos))

        if action == convert_action:
            # 发射转换章节信号
            self.convert_chapter_requested.emit(chapter_data['start_chunk'], chapter_data['end_chunk'])

    def load_chapters(self, book_id: int, current_chunk: Optional[int] = None):
        """
        加载章节列表

        Args:
            book_id: 书籍ID
            current_chunk: 当前播放的chunk（用于高亮）
        """
        from novel_reader.core import get_book_chapters, get_book
        from novel_reader.utils import load_txt_file, parse_txt

        self.current_book_id = book_id
        self.chapters_tree.clear()
        self.chapters = []

        chapters = get_book_chapters(book_id)

        if not chapters:
            item = QTreeWidgetItem(["暂无章节", "-"])
            item.setTextAlignment(0, Qt.AlignCenter)
            item.setTextAlignment(1, Qt.AlignCenter)
            self.chapters_tree.addTopLevelItem(item)
            return

        # 获取总chunk数
        book = get_book(book_id)
        if not book:
            return

        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)
        total_chunks = len(chunks)

        # 保存章节数据并创建树项
        for i, chapter in enumerate(chapters):
            start_chunk = chapter['start_chunk']

            # 计算章节的结束chunk位置
            if i + 1 < len(chapters):
                end_chunk = chapters[i + 1]['start_chunk']
            else:
                end_chunk = total_chunks

            # 保存章节数据（包含结束位置）
            chapter_data = {
                'id': chapter['id'],
                'title': chapter['title'],
                'start_chunk': start_chunk,
                'end_chunk': end_chunk,
                'chunk_count': end_chunk - start_chunk
            }
            self.chapters.append(chapter_data)

            # 创建树项
            item = QTreeWidgetItem([
                chapter['title'],
                f"{chapter_data['chunk_count']}"
            ])

            # 在第0列存储 start_chunk（使用 UserRole）
            item.setData(0, Qt.UserRole, start_chunk)

            self.chapters_tree.addTopLevelItem(item)

        # 如果提供了当前chunk，高亮对应的章节
        if current_chunk is not None:
            self.highlight_current_chapter(current_chunk)

    def clear(self):
        """清空列表"""
        self.chapters_tree.clear()
        self.current_book_id = None
        self.chapters = []

    def highlight_current_chapter(self, current_chunk: int):
        """
        高亮当前播放的章节

        Args:
            current_chunk: 当前播放的 chunk ID
        """
        if not self.chapters:
            return

        # 找到包含当前 chunk 的章节
        target_index = -1
        for i, chapter in enumerate(self.chapters):
            if chapter['start_chunk'] <= current_chunk < chapter['end_chunk']:
                target_index = i
                break

        if target_index < 0:
            return

        # 清除所有项目的高亮
        for i in range(self.chapters_tree.topLevelItemCount()):
            item = self.chapters_tree.topLevelItem(i)
            # 移除自定义的高亮属性
            item.setData(0, Qt.UserRole + 1, None)

        # 高亮目标章节
        target_item = self.chapters_tree.topLevelItem(target_index)
        if target_item:
            # 设置自定义的高亮属性
            target_item.setData(0, Qt.UserRole + 1, "current-chapter")
            # 重新绘制以应用样式
            self.chapters_tree.viewport().update()

            # 滚动到该项，使其可见
            self.chapters_tree.scrollToItem(target_item)
            # 确保该项完全可见
            self.chapters_tree.setCurrentItem(target_item)
