"""
阅读模式组件 - 纯文本阅读模式，无语音
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollBar, QPushButton, QSpinBox, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QSizePolicy
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont, QTextCursor
from typing import Optional


class ReaderWidget(QWidget):
    """阅读模式组件 - 纯文本阅读"""

    # 信号定义
    progress_changed = Signal(int, int)  # (current_position, total_length)
    chapter_changed = Signal(int)  # 章节改变信号

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.current_chapter_index: int = -1  # 当前章节索引
        self.chapters = []  # 章节列表
        self.chapter_texts = []  # 章节文本列表

        # 设置扩展策略，让组件能够占据全部可用空间
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ==================== 顶部工具栏 ====================
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 5px;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 3, 10, 3)  # 减小边距

        # 标题
        title_label = QLabel("📖 阅读模式")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        toolbar_layout.addWidget(title_label)

        # 当前章节标题
        self.chapter_title_label = QLabel("未选择书籍")
        self.chapter_title_label.setStyleSheet("font-size: 12px; color: #6c757d;")  # 减小字体
        toolbar_layout.addWidget(self.chapter_title_label)

        toolbar_layout.addStretch()

        # 显示/隐藏章节列表按钮
        self.toggle_chapter_list_btn = QPushButton("📋 目录")
        self.toggle_chapter_list_btn.setStyleSheet("""
            QPushButton {
                padding: 3px 8px;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """)
        self.toggle_chapter_list_btn.setCheckable(True)
        self.toggle_chapter_list_btn.setChecked(False)
        self.toggle_chapter_list_btn.clicked.connect(self._toggle_chapter_list)
        toolbar_layout.addWidget(self.toggle_chapter_list_btn)

        toolbar_layout.addStretch()

        # 设置 toolbar 为固定高度
        toolbar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        toolbar.setMaximumHeight(40)  # 固定最大高度

        # 字体大小控制
        font_label = QLabel("字号:")
        font_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(font_label)

        self.font_spinbox = QSpinBox()
        self.font_spinbox.setRange(12, 32)
        self.font_spinbox.setValue(16)
        self.font_spinbox.setSuffix(" px")
        self.font_spinbox.setStyleSheet("width: 80px;")
        self.font_spinbox.valueChanged.connect(self._on_font_size_changed)
        toolbar_layout.addWidget(self.font_spinbox)

        # 行间距控制
        line_spacing_label = QLabel("行距:")
        line_spacing_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(line_spacing_label)

        self.line_spacing_spinbox = QSpinBox()
        self.line_spacing_spinbox.setRange(100, 250)
        self.line_spacing_spinbox.setValue(180)
        self.line_spacing_spinbox.setSuffix("%")
        self.line_spacing_spinbox.setStyleSheet("width: 80px;")
        self.line_spacing_spinbox.valueChanged.connect(self._on_line_spacing_changed)
        toolbar_layout.addWidget(self.line_spacing_spinbox)

        layout.addWidget(toolbar)

        # ==================== 主内容区域（分割器） ====================
        content_splitter = QSplitter(Qt.Horizontal)

        # 设置 content_splitter 能够扩展占据大部分空间
        content_splitter.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # ==================== 左侧：章节列表（可折叠） ====================
        self.chapter_list = QListWidget()
        self.chapter_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                border-right: 1px solid #dee2e6;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        self.chapter_list.setMaximumWidth(250)
        self.chapter_list.setMinimumWidth(150)
        self.chapter_list.currentRowChanged.connect(self._on_chapter_selected)

        # 默认隐藏章节列表，让文本占据全部空间
        self.chapter_list.setVisible(False)
        content_splitter.addWidget(self.chapter_list)

        # ==================== 右侧：文本显示区域 ====================
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlainText("请选择一本书开始阅读")

        # 设置扩展策略，让文本显示区域能够占据全部空间
        self.text_display.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self._update_text_style()
        text_layout.addWidget(self.text_display)

        # ==================== 底部导航栏 ====================
        navbar = QFrame()
        navbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 3px;
            }
        """)
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(10, 3, 10, 3)  # 减小边距

        # 章节导航按钮
        self.prev_chapter_btn = QPushButton("◀ 上一章")
        self.prev_chapter_btn.setStyleSheet("""
            QPushButton {
                padding: 3px 12px;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
            }
        """)
        self.prev_chapter_btn.clicked.connect(self._prev_chapter)
        navbar_layout.addWidget(self.prev_chapter_btn)

        # 章节进度信息
        self.chapter_progress_label = QLabel("0 / 0 章")
        self.chapter_progress_label.setStyleSheet("color: #6c757d; font-size: 11px;")  # 减小字体
        navbar_layout.addWidget(self.chapter_progress_label)

        navbar_layout.addStretch()

        self.next_chapter_btn = QPushButton("下一章 ▶")
        self.next_chapter_btn.setStyleSheet("""
            QPushButton {
                padding: 3px 12px;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
            }
        """)
        self.next_chapter_btn.clicked.connect(self._next_chapter)
        navbar_layout.addWidget(self.next_chapter_btn)

        # 设置 navbar 为固定高度
        navbar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        navbar.setMaximumHeight(45)  # 固定最大高度

        text_layout.addWidget(navbar)

        content_splitter.addWidget(text_container)

        # 设置拉伸比例
        content_splitter.setStretchFactor(0, 0)  # 章节列表不拉伸
        content_splitter.setStretchFactor(1, 1)  # 文本区域拉伸

        layout.addWidget(content_splitter)

    def _update_text_style(self):
        """更新文本样式"""
        font_size = self.font_spinbox.value()
        line_spacing = self.line_spacing_spinbox.value() / 100.0

        self.text_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                border: none;
                padding: 15px;  # 减小内边距，增大显示区域
                font-family: 'Microsoft YaHei UI', 'SimHei', sans-serif;
                font-size: {font_size}px;
                line-height: {line_spacing};
                color: #212529;
            }}
        """)

    def load_book(self, book_id: int, current_chunk: Optional[int] = None):
        """
        加载书籍进行阅读

        Args:
            book_id: 书籍ID
            current_chunk: 当前播放的chunk（可选，用于同步播放位置）
        """
        self.current_book_id = book_id

        if book_id is None:
            self.text_display.setPlainText("未选择书籍")
            self._clear_chapters()
            return

        try:
            from novel_reader.core import get_book, get_book_chapters
            from novel_reader.utils.parser import parse_txt_preserve_format

            book = get_book(book_id)
            if book is None:
                self.text_display.setPlainText("书籍不存在")
                self._clear_chapters()
                return

            # 使用数据库中的章节信息（包含正确的 TTS chunk 范围）
            db_chapters = get_book_chapters(book_id)

            # 使用新的解析方法获取章节文本（保留原始格式）
            chapter_texts, _ = parse_txt_preserve_format(book['file_path'])

            # 验证章节数量匹配
            if db_chapters and len(db_chapters) != len(chapter_texts):
                print(f"[WARNING] 章节数量不匹配：数据库 {len(db_chapters)} 个，解析文件 {len(chapter_texts)} 个")
                print(f"[WARNING] 使用数据库的章节信息，但文本可能有偏差")

            self.chapter_texts = chapter_texts

            # 使用数据库中的章节信息（有正确的 start_chunk 用于查找）
            if db_chapters:
                self.chapters = db_chapters
                print(f"[INFO] 阅读模式：加载了 {len(db_chapters)} 个章节")
            else:
                # 如果数据库没有章节信息，创建虚拟章节
                self.chapters = [{
                    'id': 0,
                    'title': book['title'],
                    'start_chunk': 0
                }]
                print(f"[INFO] 阅读模式：数据库无章节信息，使用虚拟章节")

            # 根据当前播放chunk找到对应章节
            if current_chunk is not None:
                # 使用传入的当前播放chunk
                self._find_chapter_by_chunk(current_chunk)
                print(f"[INFO] 阅读模式：根据播放位置 chunk {current_chunk} 加载章节 {self.current_chapter_index + 1}")
            else:
                # 使用书籍的当前chunk（从数据库读取）
                book_current_chunk = book.get('current_chunk', 0)
                self._find_chapter_by_chunk(book_current_chunk)
                print(f"[INFO] 阅读模式：根据数据库位置 chunk {book_current_chunk} 加载章节 {self.current_chapter_index + 1}")

            # 更新章节列表
            self._update_chapter_list()

            # 显示当前章节
            if self.current_chapter_index >= 0:
                self._display_chapter(self.current_chapter_index)

        except Exception as e:
            self.text_display.setPlainText(f"加载失败: {str(e)}")
            self._clear_chapters()
            print(f"[ERROR] Failed to load book for reading: {e}")

    def _clear_chapters(self):
        """清空章节信息"""
        self.chapters = []
        self.chapter_texts = []
        self.current_chapter_index = -1
        self.chapter_list.clear()
        self.chapter_title_label.setText("未选择书籍")
        self._update_chapter_buttons()

    def _update_chapter_list(self):
        """更新章节列表显示"""
        self.chapter_list.clear()

        for i, chapter in enumerate(self.chapters):
            item = QListWidgetItem(f"{i + 1}. {chapter['title']}")
            item.setData(Qt.UserRole, i)  # 保存章节索引
            self.chapter_list.addItem(item)

        # 高亮当前章节
        if self.current_chapter_index >= 0:
            self.chapter_list.setCurrentRow(self.current_chapter_index)

    def _display_chapter(self, chapter_index: int):
        """
        显示指定章节

        Args:
            chapter_index: 章节索引
        """
        # 安全检查
        if chapter_index < 0:
            chapter_index = 0
        if chapter_index >= len(self.chapters):
            chapter_index = len(self.chapters) - 1
        if chapter_index >= len(self.chapter_texts):
            print(f"[ERROR] 章节索引 {chapter_index} 超出范围 (chapter_texts 长度: {len(self.chapter_texts)})")
            return

        self.current_chapter_index = chapter_index
        chapter = self.chapters[chapter_index]

        # 更新标题
        self.chapter_title_label.setText(f"第 {chapter_index + 1} 章：{chapter['title']}")

        # 显示文本
        self.text_display.setPlainText(self.chapter_texts[chapter_index])

        # 滚动到顶部
        self.text_display.verticalScrollBar().setValue(0)

        # 更新按钮状态
        self._update_chapter_buttons()

        # 保存阅读位置
        self._save_chapter_position()

        # 发射信号
        self.chapter_changed.emit(chapter_index)

    def _save_chapter_position(self):
        """保存当前章节位置"""
        if self.current_book_id is None or self.current_chapter_index < 0:
            return

        try:
            from novel_reader.core import update_book_reading_position
            # 保存当前章节的起始位置
            chapter = self.chapters[self.current_chapter_index]
            update_book_reading_position(self.current_book_id, chapter['start_chunk'])
        except Exception as e:
            print(f"[ERROR] Failed to save reading position: {e}")

    def _find_chapter_by_chunk(self, chunk: int):
        """根据 chunk 索引查找对应的章节

        Args:
            chunk: chunk 索引
        """
        if not self.chapters:
            self.current_chapter_index = -1
            return

        # 找到包含该 chunk 的章节
        for i, chapter in enumerate(self.chapters):
            # 检查这个章节是否包含该 chunk
            chapter_start = chapter['start_chunk']

            # 计算章节结束位置（下一章的起始，或全书末尾）
            if i + 1 < len(self.chapters):
                chapter_end = self.chapters[i + 1]['start_chunk']
            else:
                chapter_end = float('inf')  # 最后一章包含所有后续 chunks

            # 如果 chunk 在这个章节的范围内
            if chapter_start <= chunk < chapter_end:
                self.current_chapter_index = i
                return

        # 如果没找到，使用第一章
        self.current_chapter_index = 0

    @Slot(int)
    def _on_chapter_selected(self, row: int):
        """章节列表选中事件"""
        if row >= 0 and row < len(self.chapters):
            self._display_chapter(row)

    def _prev_chapter(self):
        """上一章"""
        if self.current_chapter_index > 0:
            self._display_chapter(self.current_chapter_index - 1)

    def _next_chapter(self):
        """下一章"""
        if self.current_chapter_index < len(self.chapters) - 1:
            self._display_chapter(self.current_chapter_index + 1)

    def _update_chapter_buttons(self):
        """更新章节导航按钮状态和进度标签"""
        self.prev_chapter_btn.setEnabled(self.current_chapter_index > 0)
        self.next_chapter_btn.setEnabled(self.current_chapter_index < len(self.chapters) - 1)

        # 更新进度标签（使用实际章节数量）
        if len(self.chapter_texts) > 0:
            # 确保 current_chapter_index 在有效范围内
            display_index = min(self.current_chapter_index, len(self.chapter_texts) - 1)
            self.chapter_progress_label.setText(
                f"{display_index + 1} / {len(self.chapter_texts)} 章"
            )
        else:
            self.chapter_progress_label.setText("0 / 0 章")

    def _toggle_chapter_list(self):
        """切换章节列表显示/隐藏"""
        is_visible = self.toggle_chapter_list_btn.isChecked()
        self.chapter_list.setVisible(is_visible)

        # 更新按钮文本
        if is_visible:
            self.toggle_chapter_list_btn.setText("📋 隐藏目录")
        else:
            self.toggle_chapter_list_btn.setText("📋 目录")

        # 更新分割器大小，让文本占据全部空间
        # 需要获取父级分割器
        parent = self.chapter_list.parent()
        if parent and isinstance(parent, QSplitter):
            if is_visible:
                # 显示章节列表，设置合理的比例
                parent.setSizes([200, parent.width() - 200])
            else:
                # 隐藏章节列表，文本占据全部空间
                parent.setSizes([0, parent.width()])

    def _on_font_size_changed(self, value: int):
        """字体大小改变"""
        self._update_text_style()

    def _on_line_spacing_changed(self, value: int):
        """行间距改变"""
        self._update_text_style()

    def save_reading_position(self):
        """保存当前阅读位置（供外部调用）"""
        self._save_chapter_position()

    def jump_to_chapter(self, chapter_index: int):
        """
        跳转到指定章节

        Args:
            chapter_index: 章节索引
        """
        if 0 <= chapter_index < len(self.chapters):
            self._display_chapter(chapter_index)

    def clear(self):
        """清空显示"""
        self.text_display.setPlainText("请选择一本书开始阅读")
        self._clear_chapters()
        self.current_book_id = None
