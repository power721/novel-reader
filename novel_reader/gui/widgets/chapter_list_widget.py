"""
章节列表组件 - 显示书籍的章节列表
"""
from PySide6.QtGui import QColor
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
    play_chapter_requested = Signal(int)  # 请求播放章节，参数：start_chunk
    convert_chapter_requested = Signal(int, int)  # 请求转换章节，参数：start_chunk, end_chunk
    enter_reading_mode_requested = Signal(int, int)  # 请求进入阅读模式，参数：start_chunk, chapter_index

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
            QTreeWidget::item:hover {
                background-color: #e8f4fd;
            }
            QTreeWidget::item:selected {
                background-color: #308cc6;
                color: white;
            }
            QTreeWidget::item[current-chapter] {
                background-color: #c8e6c9;
                color: #1b5e20;
                font-weight: bold;
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

        # 找到对应的章节数据和索引
        chapter_data = None
        chapter_index = -1
        for i, chapter in enumerate(self.chapters):
            if chapter['start_chunk'] == start_chunk:
                chapter_data = chapter
                chapter_index = i
                break

        if not chapter_data:
            return

        # 创建右键菜单
        menu = QMenu(self)

        # 播放章节
        play_action = menu.addAction("▶️ 播放本章节")
        play_action.setToolTip(f"播放《{chapter_data['title']}》")

        # 转换章节
        convert_action = menu.addAction("🔄 转换本章节 TTS")
        convert_action.setToolTip(f"转换《{chapter_data['title']}》的所有 {chapter_data['chunk_count']} 个分段")

        # 进入阅读模式
        enter_reading_mode_action = menu.addAction("📖 进入阅读模式")
        enter_reading_mode_action.setToolTip(f"在阅读模式中打开《{chapter_data['title']}》")

        # 显示菜单并获取用户选择
        action = menu.exec_(self.chapters_tree.mapToGlobal(pos))

        if action == play_action:
            # 发射播放章节信号
            self.play_chapter_requested.emit(chapter_data['start_chunk'])
        elif action == convert_action:
            # 发射转换章节信号
            self.convert_chapter_requested.emit(chapter_data['start_chunk'], chapter_data['end_chunk'])
        elif action == enter_reading_mode_action:
            # 发射进入阅读模式信号（传入章节起始位置和章节索引）
            self.enter_reading_mode_requested.emit(chapter_data['start_chunk'], chapter_index)

    def load_chapters(self, book_id: int, current_chunk: Optional[int] = None):
        """
        加载章节列表

        Args:
            book_id: 书籍ID
            current_chunk: 当前播放的chunk（用于高亮）
        """
        from novel_reader.core import get_book_chapters, get_book

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

        # 使用带缓存的解析方法
        from novel_reader.utils import parse_txt_cached
        chunks, _ = parse_txt_cached(book_id, book)
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
            self.highlight_current_chapter(current_chunk, book_id == self.get_playing_book_id())

    def clear(self):
        """清空列表"""
        self.chapters_tree.clear()
        self.current_book_id = None
        self.chapters = []

    def get_playing_book_id(self) -> Optional[int]:
        """
        获取当前正在播放的书籍ID

        Returns:
            正在播放的书籍ID，如果没有正在播放则返回None
        """
        # 通过parent层级查找MainWindow
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'playback_worker') and parent.playback_worker is not None:
                if parent.playback_worker.isRunning():
                    return parent.playback_worker.book_id
            parent = parent.parent()
        return None

    def highlight_current_chapter(self, current_chunk: int, playing: bool = True):
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
            for col in range(item.columnCount()):
                item.setData(col, Qt.BackgroundRole, None)
                item.setData(col, Qt.ForegroundRole, None)
            title = item.text(0)
            if title.startswith("▶️ "):
                item.setText(0, title[2:].strip())

        # 高亮目标章节
        target_item = self.chapters_tree.topLevelItem(target_index)
        if target_item:
            # 设置自定义的高亮属性
            target_item.setData(0, Qt.UserRole + 1, "current-chapter")
            for col in range(target_item.columnCount()):
                target_item.setBackground(col, QColor("#e8f5e9"))
                if col == 0:  # 书名列使用深绿色文字
                    target_item.setForeground(col, QColor("#1b5e20"))
            if playing:
                title = target_item.text(0)
                target_item.setText(0, f"▶️ {title}")
            # 重新绘制以应用样式
            self.chapters_tree.viewport().update()

            # 滚动到该项，使其可见
            self.chapters_tree.scrollToItem(target_item)
            # 确保该项完全可见
            self.chapters_tree.setCurrentItem(target_item)
