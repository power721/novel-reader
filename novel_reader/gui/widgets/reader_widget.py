"""
阅读模式组件 - 纯文本阅读模式，无语音
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollBar, QPushButton, QSpinBox, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QSizePolicy, QComboBox, QMenu, QDialog
)
from PySide6.QtCore import Signal, Slot, Qt, QPoint, QTimer
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat
from typing import Optional


class ReaderWidget(QWidget):
    """阅读模式组件 - 纯文本阅读"""

    # 主题样式定义
    THEMES = {
        "light": {
            "bg_color": "#f8f9fa",
            "border_color": "#dee2e6",
            "text_bg": "#ffffff",
            "text_color": "#212529",
            "title_color": "#495057",
            "subtitle_color": "#6c757d",
            "button_bg": "#e9ecef",
            "button_hover": "#dee2e6",
            "button_border": "#ced4da",
            "list_bg": "#f8f9fa",
            "list_item_hover": "#e9ecef",
            "list_item_selected": "#007bff",
            "list_item_selected_text": "white",
        },
        "dark": {
            "bg_color": "#1e1e1e",
            "border_color": "#3a3a3a",
            "text_bg": "#2b2b2b",
            "text_color": "#e0e0e0",
            "title_color": "#c0c0c0",
            "subtitle_color": "#a0a0a0",
            "button_bg": "#3a3a3a",
            "button_hover": "#4a4a4a",
            "button_border": "#4a4a4a",
            "list_bg": "#252525",
            "list_item_hover": "#3a3a3a",
            "list_item_selected": "#2a82da",
            "list_item_selected_text": "white",
        },
        "eye_protection": {
            "bg_color": "#f4ecd8",
            "border_color": "#d4c9b0",
            "text_bg": "#faf8f3",
            "text_color": "#5c4033",
            "title_color": "#8b6914",
            "subtitle_color": "#9a8b7a",
            "button_bg": "#e8dcc8",
            "button_hover": "#d9cbb5",
            "button_border": "#c9bba0",
            "list_bg": "#f0e6d0",
            "list_item_hover": "#e8dcc8",
            "list_item_selected": "#c9a227",
            "list_item_selected_text": "#5c4033",
        }
    }

    # 主题显示名称
    THEME_NAMES = {
        "light": "☀️ 日间模式",
        "dark": "🌙 夜间模式",
        "eye_protection": "🌿 护眼模式"
    }

    # 信号定义
    progress_changed = Signal(int, int)  # (current_position, total_length)
    chapter_changed = Signal(int)  # 章节改变信号
    exit_reading_mode_requested = Signal()  # 请求退出阅读模式信号
    play_chapter_requested = Signal(int)  # 请求播放章节音频，参数：start_chunk

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_book_id: Optional[int] = None
        self.current_book_title: str = ""  # 当前书籍标题
        self.current_chapter_index: int = -1  # 当前章节索引
        self.chapters = []  # 章节列表
        self.chapter_texts = []  # 章节文本列表

        # 阅读计时相关
        self._reading_timer = QTimer(self)
        self._reading_timer.timeout.connect(self._on_reading_timer_tick)
        self._session_reading_seconds = 0  # 本次会话阅读时长（秒）
        self._total_reading_seconds = 0  # 总阅读时长（秒）
        self._unsaved_seconds = 0  # 未保存到数据库的秒数
        self._is_timer_running = False

        # 自动滚动相关
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.timeout.connect(self._on_auto_scroll_tick)
        self._is_auto_scrolling = False  # 是否正在自动滚动
        self._scroll_speed = 1000  # 滚动间隔（毫秒），默认1秒
        self._scroll_lines_per_tick = 1  # 每次滚动的行数

        # 从配置加载阅读模式设置
        from novel_reader.core import settings as settings_module
        self._from_settings_scroll_speed = settings_module.get_setting("reader_auto_scroll_speed", 1000)  # 从配置读取
        self.font_size = settings_module.get_setting("reader_font_size", 14)
        self.line_spacing = settings_module.get_setting("reader_line_spacing", 100)
        self.theme = settings_module.get_setting("reader_theme", "light")  # 当前主题
        self.show_chapter_list = settings_module.get_setting("reader_show_chapter_list", True)  # 是否显示目录

        # 设置扩展策略，让组件能够占据全部可用空间
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self._setup_ui()

        # 应用初始主题
        self._apply_theme()

        # 根据配置设置目录显示状态
        self.chapter_list.setVisible(self.show_chapter_list)

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ==================== 顶部工具栏 ====================
        self.toolbar = QFrame()
        self.toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 5px;
            }
        """)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 3, 10, 3)  # 减小边距

        # 标题
        self.title_label = QLabel("📖 阅读模式")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        toolbar_layout.addWidget(self.title_label)

        # 当前章节标题
        self.chapter_title_label = QLabel("未选择书籍")
        self.chapter_title_label.setStyleSheet("font-size: 12px; color: #6c757d;")  # 减小字体
        toolbar_layout.addWidget(self.chapter_title_label)

        toolbar_layout.addStretch()

        # 显示/隐藏章节列表按钮
        # 根据配置设置按钮初始状态
        btn_text = "📋 隐藏目录" if self.show_chapter_list else "📋 显示目录"
        self.toggle_chapter_list_btn = QPushButton(btn_text)
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
        self.toggle_chapter_list_btn.setChecked(self.show_chapter_list)  # 根据配置设置
        self.toggle_chapter_list_btn.clicked.connect(self._toggle_chapter_list)
        toolbar_layout.addWidget(self.toggle_chapter_list_btn)

        # 退出阅读模式按钮
        self.exit_reading_mode_btn = QPushButton("🚪 退出阅读")
        self.exit_reading_mode_btn.setStyleSheet("""
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
        self.exit_reading_mode_btn.clicked.connect(self._exit_reading_mode)
        toolbar_layout.addWidget(self.exit_reading_mode_btn)

        # 阅读统计按钮
        self.stats_btn = QPushButton("📊 统计")
        self.stats_btn.setStyleSheet("""
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
        self.stats_btn.setCheckable(False)
        self.stats_btn.clicked.connect(self._show_stats_dialog)
        toolbar_layout.addWidget(self.stats_btn)

        toolbar_layout.addSpacing(20)

        # 自动滚动控制组
        # 开始/停止自动滚动按钮
        self.auto_scroll_btn = QPushButton("📜 自动滚动")
        self.auto_scroll_btn.setStyleSheet("""
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
            QPushButton:checked {
                background-color: #28a745;
                color: white;
                border: 1px solid #218838;
            }
        """)
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        toolbar_layout.addWidget(self.auto_scroll_btn)

        # 滚动速度控制
        scroll_speed_label = QLabel("速度:")
        scroll_speed_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(scroll_speed_label)

        self.scroll_speed_slider = QSpinBox()
        self.scroll_speed_slider.setRange(100, 3000)
        self.scroll_speed_slider.setValue(self._from_settings_scroll_speed)
        self.scroll_speed_slider.setSuffix(" ms")
        self.scroll_speed_slider.setSingleStep(100)
        self.scroll_speed_slider.setStyleSheet("width: 50px;")
        self.scroll_speed_slider.setToolTip("滚动间隔（毫秒），越小越快")
        self.scroll_speed_slider.valueChanged.connect(self._on_scroll_speed_changed)
        toolbar_layout.addWidget(self.scroll_speed_slider)

        toolbar_layout.addStretch()

        # 设置 toolbar 为固定高度
        self.toolbar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        self.toolbar.setMaximumHeight(40)  # 固定最大高度

        # 字体大小控制
        font_label = QLabel("字号:")
        font_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(font_label)

        self.font_spinbox = QSpinBox()
        self.font_spinbox.setRange(12, 32)
        self.font_spinbox.setValue(self.font_size)
        self.font_spinbox.setSuffix(" px")
        self.font_spinbox.setStyleSheet("width: 80px;")
        self.font_spinbox.valueChanged.connect(self._on_font_size_changed)
        toolbar_layout.addWidget(self.font_spinbox)

        # 行间距控制
        line_spacing_label = QLabel("行距:")
        line_spacing_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(line_spacing_label)

        self.line_spacing_spinbox = QSpinBox()
        self.line_spacing_spinbox.setRange(50, 250)
        self.line_spacing_spinbox.setValue(self.line_spacing)
        self.line_spacing_spinbox.setSuffix("%")
        self.line_spacing_spinbox.setStyleSheet("width: 80px;")
        self.line_spacing_spinbox.valueChanged.connect(self._on_line_spacing_changed)
        toolbar_layout.addWidget(self.line_spacing_spinbox)

        toolbar_layout.addSpacing(20)

        # 主题选择下拉菜单
        theme_label = QLabel("主题:")
        theme_label.setStyleSheet("color: #6c757d;")
        toolbar_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(96)
        self.theme_combo.setStyleSheet("font-size: 12px;")
        # 添加主题选项
        for theme_key in ["light", "eye_protection", "dark"]:
            self.theme_combo.addItem(self.THEME_NAMES[theme_key], theme_key)
        # 设置当前主题
        index = self.theme_combo.findData(self.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        toolbar_layout.addWidget(self.theme_combo)

        layout.addWidget(self.toolbar)

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
        self.chapter_list.setMaximumWidth(400)
        self.chapter_list.setMinimumWidth(250)
        self.chapter_list.currentRowChanged.connect(self._on_chapter_selected)

        # 启用自定义右键菜单
        self.chapter_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chapter_list.customContextMenuRequested.connect(self._show_chapter_context_menu)

        # 默认隐藏章节列表，让文本占据全部空间
        # self.chapter_list.setVisible(False)
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
        self.navbar = QFrame()
        self.navbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 3px;
            }
        """)
        navbar_layout = QHBoxLayout(self.navbar)
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

        # 章节进度信息（包含百分比）
        self.chapter_progress_label = QLabel("0 / 0 章 (0%)")
        self.chapter_progress_label.setStyleSheet("color: #6c757d; font-size: 11px;")  # 减小字体
        navbar_layout.addWidget(self.chapter_progress_label)

        # 本次阅读时长
        self.session_time_label = QLabel("本次阅读: 0分钟")
        self.session_time_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        navbar_layout.addWidget(self.session_time_label)

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
        self.navbar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        self.navbar.setMaximumHeight(35)  # 固定最大高度

        text_layout.addWidget(self.navbar)

        content_splitter.addWidget(text_container)

        # 设置拉伸比例
        content_splitter.setStretchFactor(0, 0)  # 章节列表不拉伸
        content_splitter.setStretchFactor(1, 1)  # 文本区域拉伸

        # 设置初始大小：章节列表默认显示（250px），文本区域占据剩余空间
        content_splitter.setSizes([250, 550])

        layout.addWidget(content_splitter)

    def _update_text_style(self):
        """更新文本样式"""
        font_size = self.font_spinbox.value()
        line_spacing_percent = self.line_spacing_spinbox.value()
        theme = self.THEMES[self.theme]

        # 使用 QFont 设置字号
        font = self.text_display.font()
        font.setPointSize(font_size)
        font.setFamily('Microsoft YaHei UI, SimHei, sans-serif')
        self.text_display.setFont(font)

        # 使用 QTextBlockFormat 设置行距
        cursor = self.text_display.textCursor()
        format = QTextBlockFormat()
        # 使用 ProportionalSpacing (值 = 1)
        format.setLineHeight(line_spacing_percent, 1)

        # 应用到整个文档
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(format)
        cursor.clearSelection()

        # 设置样式表（使用主题颜色）
        self.text_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg_color']};
                border: none;
                padding: 15px;
                color: {theme['text_color']};
            }}
            QScrollBar:vertical {{
                background-color: {theme['bg_color']};
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['button_border']};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['button_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def load_book(self, book_id: int, current_chunk: Optional[int] = None, preserve_position: bool = False):
        """
        加载书籍进行阅读

        Args:
            book_id: 书籍ID
            current_chunk: 当前播放的chunk（可选，用于同步播放位置）
            preserve_position: 是否保持当前阅读位置（True=不重新定位章节）
        """
        # 如果是同一本书且要求保持位置，只更新书籍ID，不重新加载
        if preserve_position and book_id == self.current_book_id and self.chapters:
            print(f"[INFO] 阅读模式：保持当前阅读位置（章节 {self.current_chapter_index + 1}）")
            return

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

            # 保存书籍标题
            self.current_book_title = book['title']

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

            # 根据当前播放chunk找到对应章节（如果不要求保持位置）
            if not preserve_position:
                # 优先使用阅读模式的独立章节记录
                reading_chapter = book.get('reading_chapter', -1)

                if reading_chapter >= 0:
                    # 使用阅读模式的章节记录
                    self.current_chapter_index = reading_chapter
                    print(f"[INFO] 阅读模式：加载上次阅读章节 {self.current_chapter_index + 1}")
                elif current_chunk is not None:
                    # 首次进入阅读模式，使用音频位置同步一次
                    self._find_chapter_by_chunk(current_chunk)
                    # 保存同步的章节作为阅读模式的初始章节
                    self._save_chapter_position()
                    print(f"[INFO] 阅读模式：首次加载，根据播放位置 chunk {current_chunk} 加载章节 {self.current_chapter_index + 1}")
                else:
                    # 使用书籍的当前chunk（从数据库读取）
                    book_current_chunk = book.get('current_chunk', 0)
                    self._find_chapter_by_chunk(book_current_chunk)
                    # 保存作为阅读模式的初始章节
                    self._save_chapter_position()
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
        self.current_book_title = ""
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

        # 更新标题（书籍标题 - 章节标题）
        if self.current_book_title:
            self.chapter_title_label.setText(f"{self.current_book_title} - 第 {chapter_index + 1} 章：{chapter['title']}")
        else:
            self.chapter_title_label.setText(f"第 {chapter_index + 1} 章：{chapter['title']}")

        # 显示文本
        self.text_display.setPlainText(self.chapter_texts[chapter_index])

        # 重新应用文本样式（字号、行距等）
        self._update_text_style()

        # 滚动到顶部
        self.text_display.verticalScrollBar().setValue(0)

        # 停止自动滚动（切换章节时）
        self.stop_auto_scroll()

        # 更新按钮状态
        self._update_chapter_buttons()

        # 更新章节列表高亮状态
        if self.chapter_list.isVisible():
            self.chapter_list.setCurrentRow(self.current_chapter_index)

        # 保存阅读位置
        self._save_chapter_position()

        # 启动阅读计时器
        self._start_reading_timer()

        # 发射信号
        self.chapter_changed.emit(chapter_index)

    def _save_chapter_position(self):
        """保存当前章节位置"""
        if self.current_book_id is None or self.current_chapter_index < 0:
            return

        try:
            from novel_reader.core import update_book_reading_chapter
            # 保存阅读模式的章节索引（独立于音频模式）
            update_book_reading_chapter(self.current_book_id, self.current_chapter_index)
            print(f"[INFO] 阅读模式：保存章节位置 {self.current_chapter_index + 1}")
        except Exception as e:
            print(f"[ERROR] Failed to save reading chapter: {e}")

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

    def _show_chapter_context_menu(self, pos: QPoint):
        """显示章节列表的右键菜单"""
        # 获取点击的列表项
        item = self.chapter_list.itemAt(pos)
        if not item:
            return

        # 获取章节索引
        chapter_index = item.data(Qt.UserRole)
        if chapter_index is None or chapter_index < 0 or chapter_index >= len(self.chapters):
            return

        chapter = self.chapters[chapter_index]
        start_chunk = chapter['start_chunk']

        # 创建右键菜单
        menu = QMenu(self)

        # 播放章节音频
        play_action = menu.addAction("▶️ 播放本章节音频")
        play_action.setToolTip(f"播放《{chapter['title']}》的音频")

        # 显示菜单并获取用户选择
        action = menu.exec_(self.chapter_list.mapToGlobal(pos))

        if action == play_action:
            # 发射播放章节信号
            self.play_chapter_requested.emit(start_chunk)

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

        # 更新进度标签（包含百分比）
        if len(self.chapter_texts) > 0:
            # 确保 current_chapter_index 在有效范围内
            display_index = min(self.current_chapter_index, len(self.chapter_texts) - 1)
            total = len(self.chapter_texts)

            # 计算百分比
            percent = int((display_index + 1) / total * 100)

            self.chapter_progress_label.setText(
                f"{display_index + 1} / {total} 章 ({percent}%)"
            )
        else:
            self.chapter_progress_label.setText("0 / 0 章 (0%)")

    def _toggle_chapter_list(self):
        """切换章节列表显示/隐藏"""
        is_visible = self.toggle_chapter_list_btn.isChecked()
        self.show_chapter_list = is_visible
        self.chapter_list.setVisible(is_visible)

        # 更新按钮文本
        if is_visible:
            self.toggle_chapter_list_btn.setText("📋 隐藏目录")
        else:
            self.toggle_chapter_list_btn.setText("📋 显示目录")

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

        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_show_chapter_list", is_visible)

    def _exit_reading_mode(self):
        """退出阅读模式"""
        # 发射退出阅读模式信号
        self.exit_reading_mode_requested.emit()

    def _on_font_size_changed(self, value: int):
        """字体大小改变"""
        self.font_size = value
        self._update_text_style()
        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_font_size", value)

    def _on_line_spacing_changed(self, value: int):
        """行间距改变"""
        self.line_spacing = value
        self._update_text_style()
        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_line_spacing", value)

    def _on_theme_changed(self, index: int):
        """主题选择改变事件"""
        theme_key = self.theme_combo.itemData(index)
        if theme_key and theme_key in self.THEMES:
            self.theme = theme_key
            # 应用新主题
            self._apply_theme()
            # 保存到配置
            from novel_reader.core import settings as settings_module
            settings_module.set_setting("reader_theme", self.theme)
            print(f"[INFO] 主题已切换到: {self.THEME_NAMES[theme_key]}")

    def _apply_theme(self):
        """应用主题到整个界面"""
        theme = self.THEMES[self.theme]

        # 更新工具栏样式
        self.toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['bg_color']};
                border-bottom: 1px solid {theme['border_color']};
                padding: 5px;
            }}
        """)

        # 更新标题标签颜色
        self.title_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {theme['title_color']};")

        # 更新按钮样式
        button_style = f"""
            QPushButton {{
                padding: 3px 8px;
                background-color: {theme['button_bg']};
                border: 1px solid {theme['button_border']};
                border-radius: 4px;
                font-size: 12px;
                color: {theme['text_color']};
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QPushButton:disabled {{
                background-color: {theme['bg_color']};
                color: {theme['subtitle_color']};
            }}
        """
        self.prev_chapter_btn.setStyleSheet(button_style)
        self.next_chapter_btn.setStyleSheet(button_style)
        self.toggle_chapter_list_btn.setStyleSheet(button_style)
        self.exit_reading_mode_btn.setStyleSheet(button_style)
        self.stats_btn.setStyleSheet(button_style)

        # 更新下拉菜单和输入框样式
        combo_style = f"""
            QComboBox {{
                padding: 3px 8px;
                background-color: {theme['text_bg']};
                border: 1px solid {theme['button_border']};
                border-radius: 4px;
                font-size: 12px;
                color: {theme['text_color']};
            }}
            QComboBox:hover {{
                border: 1px solid {theme['button_hover']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['text_bg']};
                border: 1px solid {theme['button_border']};
                selection-background-color: {theme['list_item_selected']};
                selection-color: {theme['list_item_selected_text']};
                color: {theme['text_color']};
            }}
        """
        self.theme_combo.setStyleSheet(combo_style)

        spinbox_style = f"""
            QSpinBox {{
                background-color: {theme['text_bg']};
                border: 1px solid {theme['button_border']};
                border-radius: 4px;
                padding: 3px;
                color: {theme['text_color']};
            }}
            QSpinBox:focus {{
                border: 1px solid {theme['list_item_selected']};
            }}
        """
        self.font_spinbox.setStyleSheet(spinbox_style)
        self.line_spacing_spinbox.setStyleSheet(spinbox_style)

        # 更新标签颜色
        self.chapter_title_label.setStyleSheet(f"font-size: 12px; color: {theme['subtitle_color']};")
        self.chapter_progress_label.setStyleSheet(f"color: {theme['subtitle_color']}; font-size: 11px;")

        # 更新章节列表样式
        self.chapter_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme['list_bg']};
                border: none;
                border-right: 1px solid {theme['border_color']};
                padding: 5px;
                color: {theme['text_color']};
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {theme['list_item_hover']};
            }}
            QListWidget::item:selected {{
                background-color: {theme['list_item_selected']};
                color: {theme['list_item_selected_text']};
            }}
        """)

        # 更新导航栏样式
        self.navbar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['bg_color']};
                border-top: 1px solid {theme['border_color']};
                padding: 3px;
            }}
        """)

        # 更新文本显示区域样式
        self._update_text_style()

    def save_reading_position(self):
        """保存当前阅读位置（供外部调用）"""
        self._save_chapter_position()

    def stop_reading_timer(self):
        """停止阅读计时器（供外部调用）"""
        self._stop_reading_timer()

    def jump_to_chapter(self, chapter_index: int):
        """
        跳转到指定章节

        Args:
            chapter_index: 章节索引
        """
        if 0 <= chapter_index < len(self.chapters):
            self._display_chapter(chapter_index)

    def load_book_and_jump_to_chapter(self, book_id: int, chapter_index: int):
        """
        加载书籍并直接跳转到指定章节（忽略保存的阅读位置）

        Args:
            book_id: 书籍ID
            chapter_index: 章节索引（0-based）
        """
        from novel_reader.core import get_book, get_book_chapters
        from novel_reader.utils.parser import parse_txt_preserve_format

        book = get_book(book_id)
        if book is None:
            self.text_display.setPlainText("书籍不存在")
            self._clear_chapters()
            return

        self.current_book_id = book_id
        self.current_book_title = book['title']

        # 使用数据库中的章节信息
        db_chapters = get_book_chapters(book_id)

        # 获取章节文本
        chapter_texts, _ = parse_txt_preserve_format(book['file_path'])

        self.chapter_texts = chapter_texts

        # 使用数据库中的章节信息
        if db_chapters:
            self.chapters = db_chapters
        else:
            self.chapters = [{
                'id': 0,
                'title': book['title'],
                'start_chunk': 0
            }]

        # 边界检查
        if chapter_index < 0:
            chapter_index = 0
        elif chapter_index >= len(self.chapters):
            chapter_index = len(self.chapters) - 1

        if chapter_index >= len(self.chapter_texts):
            return

        # 直接设置要跳转的章节
        self.current_chapter_index = chapter_index

        # 先显示指定章节（避免信号触发导致的竞态条件）
        # 暂时断开信号，防止 setCurrentRow 触发 _on_chapter_selected
        try:
            self.chapter_list.currentRowChanged.disconnect()
            self._display_chapter(self.current_chapter_index)
            # 再更新章节列表
            self._update_chapter_list()
        finally:
            # 重新连接信号
            self.chapter_list.currentRowChanged.connect(self._on_chapter_selected)

        # 保存章节位置
        self._save_chapter_position()

    def clear(self):
        """清空显示"""
        self.text_display.setPlainText("请选择一本书开始阅读")
        self._clear_chapters()
        self.current_book_id = None
        # 停止计时器
        self._stop_reading_timer()

    # ==================== 阅读计时相关 ====================

    def _start_reading_timer(self):
        """启动阅读计时器"""
        if not self._is_timer_running:
            self._reading_timer.start(1000)  # 每秒触发一次
            self._is_timer_running = True
            # 重置本次会话时长
            self._session_reading_seconds = 0
            self._unsaved_seconds = 0
            print(f"[INFO] 阅读计时器已启动 (书籍ID: {self.current_book_id})")
            # 立即更新一次显示
            self._update_session_time_display()

    def _stop_reading_timer(self):
        """停止阅读计时器并保存时长"""
        if self._is_timer_running:
            self._reading_timer.stop()
            self._is_timer_running = False

            # 保存剩余的未保存时长到数据库
            if self.current_book_id and self._unsaved_seconds > 0:
                from novel_reader.core.book import update_book_reading_time
                update_book_reading_time(self.current_book_id, self._unsaved_seconds)
                print(f"[INFO] 已保存剩余阅读时长: {self._unsaved_seconds} 秒")

            print("[INFO] 阅读计时器已停止")

    def _on_reading_timer_tick(self):
        """计时器每秒触发"""
        self._session_reading_seconds += 1
        self._total_reading_seconds += 1
        self._unsaved_seconds += 1

        # 更新显示（每10秒更新一次显示，避免频繁刷新）
        if self._session_reading_seconds % 10 == 0:
            self._update_session_time_display()

        # 每60秒保存一次到数据库（防止数据丢失）
        if self._unsaved_seconds >= 60 and self.current_book_id:
            from novel_reader.core.book import update_book_reading_time
            # 保存60秒
            update_book_reading_time(self.current_book_id, 60)
            print(f"[INFO] 自动保存阅读时长: +60 秒 (本次会话总计: {self._session_reading_seconds} 秒)")
            # 重置未保存计数，而不是重置会话计数
            self._unsaved_seconds = 0

    def _update_session_time_display(self):
        """更新本次阅读时长显示"""
        minutes = self._session_reading_seconds // 60
        seconds = self._session_reading_seconds % 60
        if minutes > 0:
            self.session_time_label.setText(f"本次阅读: {minutes}分{seconds}秒")
        else:
            self.session_time_label.setText(f"本次阅读: {seconds}秒")

    def _load_reading_time(self):
        """从数据库加载总阅读时长"""
        if not self.current_book_id:
            self._total_reading_seconds = 0
            return

        from novel_reader.core.book import get_book_reading_stats
        stats = get_book_reading_stats(self.current_book_id)
        if stats:
            self._total_reading_seconds = stats['reading_time_seconds']
        else:
            self._total_reading_seconds = 0

    def _show_stats_dialog(self):
        """显示阅读统计对话框"""
        if not self.current_book_id:
            return

        dialog = ReadingStatsDialog(self.current_book_id, self)
        dialog.exec()

    # ==================== 自动滚动相关 ====================

    def _toggle_auto_scroll(self):
        """切换自动滚动开关"""
        self._is_auto_scrolling = self.auto_scroll_btn.isChecked()

        if self._is_auto_scrolling:
            # 启动自动滚动
            self._scroll_speed = self.scroll_speed_slider.value()
            self._auto_scroll_timer.start(self._scroll_speed)
            self.auto_scroll_btn.setText("⏸ 停止滚动")
            print(f"[INFO] 自动滚动已启动，间隔: {self._scroll_speed}ms")
        else:
            # 停止自动滚动
            self._auto_scroll_timer.stop()
            self.auto_scroll_btn.setText("📜 自动滚动")
            print("[INFO] 自动滚动已停止")

    def _on_auto_scroll_tick(self):
        """自动滚动定时器触发"""
        if not self._is_auto_scrolling:
            return

        # 获取当前滚动条
        scrollbar = self.text_display.verticalScrollBar()

        # 计算要滚动的像素值（基于字体大小）
        font_metrics = self.text_display.fontMetrics()
        line_height = font_metrics.lineSpacing()
        scroll_pixels = line_height * self._scroll_lines_per_tick

        # 向下滚动
        new_value = scrollbar.value() + scroll_pixels
        scrollbar.setValue(new_value)

        # 检查是否已滚动到底部
        if scrollbar.value() >= scrollbar.maximum():
            # 到达底部，停止自动滚动
            self._auto_scroll_timer.stop()
            self._is_auto_scrolling = False
            self.auto_scroll_btn.setChecked(False)
            self.auto_scroll_btn.setText("📜 自动滚动")
            print("[INFO] 已滚动到底部，自动滚动停止")

    def _on_scroll_speed_changed(self, value: int):
        """滚动速度改变"""
        self._scroll_speed = value

        # 如果正在自动滚动，需要重启定时器以应用新速度
        if self._is_auto_scrolling:
            self._auto_scroll_timer.setInterval(value)

        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_auto_scroll_speed", value)

    def toggle_auto_scroll_shortcut(self):
        """通过快捷键切换自动滚动"""
        self.auto_scroll_btn.click()

    def stop_auto_scroll(self):
        """停止自动滚动（供外部调用）"""
        if self._is_auto_scrolling:
            self._auto_scroll_timer.stop()
            self._is_auto_scrolling = False
            self.auto_scroll_btn.setChecked(False)
            self.auto_scroll_btn.setText("📜 自动滚动")


# ==================== 阅读统计对话框 ====================

class ReadingStatsDialog(QDialog):
    """阅读统计对话框"""

    def __init__(self, book_id: int, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        from novel_reader.core import get_book, get_book_chapters
        from novel_reader.core.book import get_book_reading_stats

        book = get_book(self.book_id)
        if not book:
            return

        stats = get_book_reading_stats(self.book_id)
        if not stats:
            return

        # 获取章节列表
        chapters = get_book_chapters(self.book_id)
        total_chapters = len(chapters) if chapters else 1

        self.setWindowTitle("📊 阅读统计")
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel(f"📖 {book['title']}")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #212529;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 计算统计信息
        current_chapter = stats.get('reading_chapter', 0) + 1
        total_reading_seconds = stats.get('reading_time_seconds', 0)
        chunk_count = stats.get('chunk_count', 0)

        # 阅读进度
        progress_percent = 0
        if total_chapters > 0:
            progress_percent = int((current_chapter / total_chapters) * 100)

        # 阅读时长格式化
        hours = total_reading_seconds // 3600
        minutes = (total_reading_seconds % 3600) // 60
        if hours > 0:
            time_str = f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            time_str = f"{minutes}分钟"
        else:
            time_str = "少于1分钟"

        # 统计信息
        stats_grid = QVBoxLayout()

        # 进度
        progress_item = self._create_stat_item(
            "📚 阅读进度",
            f"{current_chapter} / {total_chapters} 章",
            f"{progress_percent}%"
        )
        stats_grid.addLayout(progress_item)

        # 阅读时长
        time_item = self._create_stat_item(
            "⏱ 累计阅读",
            time_str,
            f"{total_reading_seconds:,} 秒"
        )
        stats_grid.addLayout(time_item)

        # 总段数
        chunks_item = self._create_stat_item(
            "📄 总段数",
            f"{chunk_count:,} 段",
            ""
        )
        stats_grid.addLayout(chunks_item)

        # 章节数
        chapters_item = self._create_stat_item(
            "📑 章节数",
            f"{total_chapters} 章",
            ""
        )
        stats_grid.addLayout(chapters_item)

        layout.addLayout(stats_grid)

        # 阅读建议
        if progress_percent < 10:
            suggestion = "💡 刚开始阅读，加油！"
        elif progress_percent < 30:
            suggestion = "💡 渐入佳境，继续保持！"
        elif progress_percent < 50:
            suggestion = "💡 已读近半，精彩继续！"
        elif progress_percent < 70:
            suggestion = "💡 已过半程，冲刺阶段！"
        elif progress_percent < 90:
            suggestion = "💡 即将完结，最后冲刺！"
        else:
            suggestion = "🎉 恭喜！即将读完全书！"

        suggestion_label = QLabel(suggestion)
        suggestion_label.setStyleSheet("font-size: 14px; color: #495057; padding: 10px; background-color: #e8f4fd; border-radius: 8px;")
        suggestion_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(suggestion_label)

        # 关闭按钮
        layout.addStretch()
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
        layout.addWidget(close_btn)

    def _create_stat_item(self, title: str, value: str, subtext: str):
        """创建统计项布局"""
        item_layout = QVBoxLayout()
        item_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        item_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        item_layout.addWidget(value_label)

        if subtext:
            subtext_label = QLabel(subtext)
            subtext_label.setStyleSheet("font-size: 11px; color: #adb5bd;")
            item_layout.addWidget(subtext_label)

        return item_layout
