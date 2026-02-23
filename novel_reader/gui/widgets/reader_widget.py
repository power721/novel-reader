"""
阅读模式组件 - 纯文本阅读模式，无语音
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollBar, QPushButton, QSpinBox, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QSizePolicy, QComboBox, QMenu, QDialog, QCheckBox
)
from PySide6.QtCore import Signal, Slot, Qt, QPoint, QTimer
from PySide6.QtGui import QFont, QTextCursor, QTextBlockFormat, QColor
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
        },
        # 起点风格主题
        "qidian_beige": {
            "bg_color": "#f7f3e8",
            "border_color": "#e0d9c8",
            "text_bg": "#faf8f3",
            "text_color": "#5c4b3a",
            "title_color": "#8b7355",
            "subtitle_color": "#a89880",
            "button_bg": "#efe8d8",
            "button_hover": "#e5ddca",
            "button_border": "#d9d1c0",
            "list_bg": "#f2ebe1",
            "list_item_hover": "#ebe4d8",
            "list_item_selected": "#c9a86c",
            "list_item_selected_text": "#5c4b3a",
        },
        "qidian_green": {
            "bg_color": "#e8f5e9",
            "border_color": "#c8e6c9",
            "text_bg": "#f1f8f3",
            "text_color": "#2e4a35",
            "title_color": "#3d5b46",
            "subtitle_color": "#6b8a73",
            "button_bg": "#dceddc",
            "button_hover": "#c8e6c9",
            "button_border": "#a5d6a7",
            "list_bg": "#e0f2e5",
            "list_item_hover": "#dceddc",
            "list_item_selected": "#66bb6a",
            "list_item_selected_text": "#1b3a24",
        },
        "qidian_blue": {
            "bg_color": "#e3f2fd",
            "border_color": "#bbdefb",
            "text_bg": "#e8f4fd",
            "text_color": "#1a3a52",
            "title_color": "#2a4a62",
            "subtitle_color": "#5a7a92",
            "button_bg": "#d0e8f8",
            "button_hover": "#c0e0f5",
            "button_border": "#a8d4f0",
            "list_bg": "#dff0f8",
            "list_item_hover": "#d0e8f8",
            "list_item_selected": "#42a5f5",
            "list_item_selected_text": "#0d2a42",
        },
        "dark": {
            "bg_color": "#1a1a1a",
            "border_color": "#333333",
            "text_bg": "#222222",
            "text_color": "#b0b0b0",
            "title_color": "#d0d0d0",
            "subtitle_color": "#808080",
            "button_bg": "#333333",
            "button_hover": "#404040",
            "button_border": "#4a4a4a",
            "list_bg": "#1f1f1f",
            "list_item_hover": "#2a2a2a",
            "list_item_selected": "#ed6a20",
            "list_item_selected_text": "white",
        },
    }

    # 主题显示名称
    THEME_NAMES = {
        "light": "☀️ 日间模式",
        "eye_protection": "🌿 护眼模式",
        "qidian_beige": "📖 米黄",
        "qidian_green": "📖 淡绿",
        "qidian_blue": "📖 淡蓝",
        "dark": "🌙 夜间模式",
    }

    # 信号定义
    progress_changed = Signal(int, int)  # (current_position, total_length)
    chapter_changed = Signal(int)  # 章节改变信号
    exit_reading_mode_requested = Signal()  # 请求退出阅读模式信号
    play_chapter_requested = Signal(int)  # 请求播放章节音频，参数：start_chunk
    switch_book_requested = Signal(int)  # 请求切换书籍，参数：book_id

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
        # 每本书籍的会话阅读时间缓存 {book_id: {'session_seconds': int, 'unsaved_seconds': int}}
        self._book_reading_cache = {}

        # 自动滚动相关
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.timeout.connect(self._on_auto_scroll_tick)
        self._is_auto_scrolling = False  # 是否正在自动滚动
        self._scroll_speed = 1000  # 滚动间隔（毫秒），默认1秒
        self._scroll_lines_per_tick = 1  # 每次滚动的行数
        self._auto_scroll_next_chapter = True  # 是否在滚动到底部时自动切换下一章
        self._waiting_to_next_chapter = False  # 是否正在等待切换到下一章
        self._pending_resume_after_chapter = False  # 是否在章节切换后待恢复滚动

        # 从配置加载阅读模式设置
        from novel_reader.core import settings as settings_module
        self._scroll_speed = settings_module.get_setting("reader_auto_scroll_speed", 1000)  # 从配置读取
        self._auto_scroll_next_chapter = settings_module.get_setting("reader_auto_scroll_next_chapter", True)  # 从配置读取自动切换下一章设置
        self._chapter_switch_delay = settings_module.get_setting("reader_chapter_switch_delay", 5000)  # 从配置读取章节切换延迟（底部停留时间）
        self._chapter_start_delay = settings_module.get_setting("reader_chapter_start_delay", 7000)  # 从配置读取章节开始延迟（新章准备时间）
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

        # 切换书籍按钮
        self.switch_book_btn = QPushButton("📚 切换书籍")
        self.switch_book_btn.setStyleSheet("""
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
        self.switch_book_btn.clicked.connect(self._show_switch_book_dialog)
        toolbar_layout.addWidget(self.switch_book_btn)

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

        # 阅读统计按钮
        self.stats_btn = QPushButton("📊 阅读统计")
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

        # 滚动设置按钮
        self.scroll_settings_btn = QPushButton("⚙️ 滚动设置")
        self.scroll_settings_btn.setStyleSheet("""
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
        self.scroll_settings_btn.clicked.connect(self._show_scroll_settings_dialog)
        toolbar_layout.addWidget(self.scroll_settings_btn)

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
        self.font_spinbox.setStyleSheet("width: 50px;")
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
        self.line_spacing_spinbox.setStyleSheet("width: 50px;")
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
        for theme_key in ["light", "eye_protection", "qidian_beige", "qidian_green", "qidian_blue", "dark"]:
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

        # 当前章节标题
        self.navbar_chapter_title_label = QLabel("")
        self.navbar_chapter_title_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        # self.navbar_chapter_title_label.setWordWrap(True)
        self.navbar_chapter_title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        navbar_layout.addWidget(self.navbar_chapter_title_label)

        # 当前章节字数
        self.chapter_word_count_label = QLabel("")
        self.chapter_word_count_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        navbar_layout.addWidget(self.chapter_word_count_label)

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
        is_same_book = (book_id == self.current_book_id)
        if preserve_position and is_same_book and self.chapters:
            print(f"[INFO] 阅读模式：保持当前阅读位置（章节 {self.current_chapter_index + 1}）")
            return

        # 如果切换到不同的书籍，先保存当前书籍的会话时间到缓存
        if not is_same_book and self.current_book_id is not None:
            if self._is_timer_running:
                print(f"[INFO] 阅读模式：切换书籍，停止当前计时器")
                self._stop_reading_timer()
            # 保存当前书籍的会话时间到缓存
            self._book_reading_cache[self.current_book_id] = {
                'session_seconds': self._session_reading_seconds,
                'unsaved_seconds': self._unsaved_seconds
            }
            print(f"[INFO] 阅读模式：已保存书籍 {self.current_book_id} 的会话时间缓存 "
                  f"({self._session_reading_seconds}秒，未保存{self._unsaved_seconds}秒)")

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

            # 从数据库加载总阅读时长
            self._load_reading_time()

            # 恢复该书籍的会话时间缓存（如果存在）
            if book_id in self._book_reading_cache:
                cached = self._book_reading_cache[book_id]
                self._session_reading_seconds = cached['session_seconds']
                self._unsaved_seconds = cached['unsaved_seconds']
                print(f"[INFO] 阅读模式：恢复书籍 {book_id} 的会话时间缓存 "
                      f"({self._session_reading_seconds}秒，未保存{self._unsaved_seconds}秒)")
            else:
                # 新书籍，重置会话时间
                self._session_reading_seconds = 0
                self._unsaved_seconds = 0
                print(f"[INFO] 阅读模式：新书籍，重置会话时间")

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
        self.navbar_chapter_title_label.setText("")
        self._update_chapter_buttons()

    def _update_chapter_list(self):
        """更新章节列表显示"""
        # 临时断开信号，防止在更新时触发 _on_chapter_selected
        try:
            self.chapter_list.currentRowChanged.disconnect(self._on_chapter_selected)
        except TypeError:
            pass  # 如果信号没有连接，忽略错误

        self.chapter_list.clear()

        for i, chapter in enumerate(self.chapters):
            item = QListWidgetItem(chapter['title'])
            item.setData(Qt.UserRole, i)  # 保存章节索引
            self.chapter_list.addItem(item)

        # 高亮当前章节
        if self.current_chapter_index >= 0:
            self.chapter_list.setCurrentRow(self.current_chapter_index)

        # 重新连接信号
        self.chapter_list.currentRowChanged.connect(self._on_chapter_selected)

    def _display_chapter(self, chapter_index: int, keep_auto_scroll: bool = False, continue_timing: bool = True):
        """
        显示指定章节

        Args:
            chapter_index: 章节索引
            keep_auto_scroll: 是否保持自动滚动状态（默认 False）
            continue_timing: 是否继续计时（默认 True，不重置计时器）
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

        # 更新工具栏标题（只显示书籍标题）
        if self.current_book_title:
            self.chapter_title_label.setText(self.current_book_title)
        else:
            self.chapter_title_label.setText(f"第 {chapter_index + 1} 章：{chapter['title']}")

        # 更新底部导航栏章节标题（只显示章节标题，去掉"第X章"）
        self.navbar_chapter_title_label.setText(chapter['title'])

        # 显示文本
        self.text_display.setPlainText(self.chapter_texts[chapter_index])

        # 重新应用文本样式（字号、行距等）
        self._update_text_style()

        # 滚动到顶部
        self.text_display.verticalScrollBar().setValue(0)

        # 停止自动滚动（切换章节时），除非要求保持自动滚动状态
        if not keep_auto_scroll:
            self.stop_auto_scroll()
        else:
            # 保持自动滚动状态，确保待恢复标志被设置
            self._pending_resume_after_chapter = True

        # 更新按钮状态
        self._update_chapter_buttons()

        # 更新章节列表高亮状态
        if self.chapter_list.isVisible():
            # 临时断开信号，防止触发 _on_chapter_selected
            try:
                self.chapter_list.currentRowChanged.disconnect(self._on_chapter_selected)
            except TypeError:
                pass
            self.chapter_list.setCurrentRow(self.current_chapter_index)
            # 重新连接信号
            self.chapter_list.currentRowChanged.connect(self._on_chapter_selected)

        # 保存阅读位置
        self._save_chapter_position()

        # 启动阅读计时器（如果需要继续计时）
        if continue_timing:
            self._continue_reading_timer()
        else:
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

    def _next_chapter(self, keep_auto_scroll: bool = False):
        """下一章

        Args:
            keep_auto_scroll: 是否保持自动滚动状态（默认 False）
        """
        if self.current_chapter_index < len(self.chapters) - 1:
            self._display_chapter(self.current_chapter_index + 1, keep_auto_scroll=keep_auto_scroll)

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

        # 更新字数标签
        if self.current_chapter_index >= 0 and self.current_chapter_index < len(self.chapters):
            chapter = self.chapters[self.current_chapter_index]
            word_count = chapter.get('word_count', 0)
            if word_count > 0:
                self.chapter_word_count_label.setText(f"{word_count}字")
            else:
                self.chapter_word_count_label.setText("")
        else:
            self.chapter_word_count_label.setText("")

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
        self.switch_book_btn.setStyleSheet(button_style)
        self.auto_scroll_btn.setStyleSheet(button_style)
        self.scroll_settings_btn.setStyleSheet(button_style)

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
        self.navbar_chapter_title_label.setStyleSheet(f"color: {theme['subtitle_color']}; font-size: 11px;")
        self.chapter_progress_label.setStyleSheet(f"color: {theme['subtitle_color']}; font-size: 11px;")
        self.chapter_word_count_label.setStyleSheet(f"color: {theme['subtitle_color']}; font-size: 11px;")
        self.session_time_label.setStyleSheet(f"color: {theme['subtitle_color']}; font-size: 11px;")

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

    def start_reading_timer(self):
        """启动阅读计时器（供外部调用）"""
        self._continue_reading_timer()

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
        """启动阅读计时器（重置会话时长）"""
        if not self._is_timer_running:
            self._reading_timer.start(1000)  # 每秒触发一次
            self._is_timer_running = True
            # 重置本次会话时长和未保存计数
            self._session_reading_seconds = 0
            self._unsaved_seconds = 0
            # 注意：_total_reading_seconds 不应该被重置，它应该在 load_book 时从数据库加载
            print(f"[INFO] 阅读计时器已启动 (书籍ID: {self.current_book_id})")
            # 立即更新一次显示
            self._update_session_time_display()

    def _continue_reading_timer(self):
        """继续阅读计时器（不重置会话时长）"""
        if not self._is_timer_running:
            self._reading_timer.start(1000)  # 每秒触发一次
            self._is_timer_running = True
            # 立即更新一次显示
            self._update_session_time_display()

    def _stop_reading_timer(self):
        """停止阅读计时器并保存时长"""
        if self._is_timer_running:
            self._reading_timer.stop()
            self._is_timer_running = False

            # 保存所有剩余的未保存时长到数据库
            if self.current_book_id and self._unsaved_seconds > 0:
                from novel_reader.core.book import update_book_reading_time
                update_book_reading_time(self.current_book_id, self._unsaved_seconds)
                # 清零未保存秒数
                self._unsaved_seconds = 0

            print(f"[INFO] 阅读计时器已停止 (本次会话: {self._session_reading_seconds} 秒)")

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
            # print(f"[INFO] 自动保存阅读时长: +60 秒 (本次会话总计: {self._session_reading_seconds} 秒)")
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

        dialog = ReadingStatsDialog(self.current_book_id, reader_widget=self, parent=self)
        dialog.exec()

    def _show_switch_book_dialog(self):
        """显示切换书籍对话框"""
        dialog = SwitchBookDialog(self.current_book_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_book_id = dialog.selected_book_id
            if new_book_id and new_book_id != self.current_book_id:
                # 发射切换书籍信号
                self.switch_book_requested.emit(new_book_id)

    def _show_scroll_settings_dialog(self):
        """显示自动滚动设置对话框"""
        dialog = AutoScrollSettingsDialog(self)
        dialog.exec()

    # ==================== 自动滚动相关 ====================

    def _toggle_auto_scroll(self):
        """切换自动滚动开关"""
        self._is_auto_scrolling = self.auto_scroll_btn.isChecked()

        if self._is_auto_scrolling:
            # 启动自动滚动
            self._auto_scroll_timer.start(self._scroll_speed)
            self.auto_scroll_btn.setText("⏸ 停止滚动")
            print(f"[INFO] 自动滚动已启动，间隔: {self._scroll_speed}ms")
        else:
            # 停止自动滚动
            self._auto_scroll_timer.stop()
            self._waiting_to_next_chapter = False  # 重置等待标志
            self._pending_resume_after_chapter = False  # 重置待恢复标志
            self.auto_scroll_btn.setText("📜 自动滚动")
            print("[INFO] 自动滚动已停止")

    def _on_auto_scroll_tick(self):
        """自动滚动定时器触发"""
        if not self._is_auto_scrolling:
            return

        # 如果正在等待切换章节，不执行滚动操作
        if self._waiting_to_next_chapter:
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
            # 到达底部
            if self._auto_scroll_next_chapter and self.current_chapter_index < len(self.chapters) - 1:
                # 启用了自动切换且不是最后一章
                # 设置等待标志，防止重复触发
                self._waiting_to_next_chapter = True

                # 停止定时器，等待3秒后切换章节
                self._auto_scroll_timer.stop()
                print(f"[INFO] 已滚动到底部，{self._chapter_switch_delay/1000:.1f}秒后自动切换到下一章...")

                # 使用 QTimer 延迟切换章节
                QTimer.singleShot(self._chapter_switch_delay, self._auto_switch_to_next_chapter)
            else:
                # 最后一章或未启用自动切换，停止自动滚动
                self._auto_scroll_timer.stop()
                self._is_auto_scrolling = False
                self.auto_scroll_btn.setChecked(False)
                self.auto_scroll_btn.setText("📜 自动滚动")
                if self.current_chapter_index >= len(self.chapters) - 1:
                    print("[INFO] 已滚动到全书末尾，自动滚动停止")
                else:
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

    def _on_auto_next_chapter_changed(self, state):
        """自动切换下一章选项改变"""
        self._auto_scroll_next_chapter = (state == Qt.CheckState.Checked.value)

        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_auto_scroll_next_chapter", self._auto_scroll_next_chapter)
        print(f"[INFO] 自动切换下一章: {'启用' if self._auto_scroll_next_chapter else '禁用'}")

    def _on_switch_delay_changed(self, value: int):
        """章节切换延迟改变（底部停留时间）"""
        self._chapter_switch_delay = value

        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_chapter_switch_delay", value)

    def _on_start_delay_changed(self, value: int):
        """章节开始延迟改变（新章准备时间）"""
        self._chapter_start_delay = value

        # 保存到配置
        from novel_reader.core import settings as settings_module
        settings_module.set_setting("reader_chapter_start_delay", value)

    def _continue_auto_scroll_after_chapter_change(self):
        """章节切换后继续自动滚动（延迟启动）"""
        # 检查是否有待恢复的滚动请求
        if self._pending_resume_after_chapter:
            print(f"[INFO] {self._chapter_start_delay/1000:.1f}秒后开始自动滚动...")
            # 延迟启动自动滚动
            QTimer.singleShot(self._chapter_start_delay, self._start_auto_scroll_now)

    def _start_auto_scroll_now(self):
        """立即启动自动滚动"""
        # 清除待恢复标志
        was_pending = self._pending_resume_after_chapter
        self._pending_resume_after_chapter = False

        if not was_pending:
            return

        # 确保自动滚动状态
        if not self._is_auto_scrolling:
            self._is_auto_scrolling = True
            self.auto_scroll_btn.setChecked(True)
            self.auto_scroll_btn.setText("⏸ 停止滚动")

        # 确保定时器在运行
        if not self._auto_scroll_timer.isActive():
            self._auto_scroll_timer.start(self._scroll_speed)
            print("[INFO] 自动滚动已继续")

    def _auto_switch_to_next_chapter(self):
        """延迟后自动切换到下一章"""
        # 重置等待标志
        self._waiting_to_next_chapter = False

        # 检查是否仍在自动滚动模式
        if not self._is_auto_scrolling:
            print("[INFO] 自动滚动已停止，取消切换章节")
            return

        # 检查是否还能切换到下一章
        if self.current_chapter_index < len(self.chapters) - 1:
            print(f"[INFO] 自动切换到下一章 (第 {self.current_chapter_index + 1} 章 -> 第 {self.current_chapter_index + 2} 章)")
            # 设置待恢复标志
            self._pending_resume_after_chapter = True
            self._next_chapter(keep_auto_scroll=True)

            # 切换到下一章后，延迟再开始滚动
            QTimer.singleShot(100, self._continue_auto_scroll_after_chapter_change)
        else:
            # 已经是最后一章（可能在等待期间发生了变化）
            self._is_auto_scrolling = False
            self._waiting_to_next_chapter = False
            self._pending_resume_after_chapter = False
            self.auto_scroll_btn.setChecked(False)
            self.auto_scroll_btn.setText("📜 自动滚动")
            print("[INFO] 已是最后一章，自动滚动停止")

    def toggle_auto_scroll_shortcut(self):
        """通过快捷键切换自动滚动"""
        self.auto_scroll_btn.click()

    def stop_auto_scroll(self):
        """停止自动滚动（供外部调用）"""
        if self._is_auto_scrolling:
            self._auto_scroll_timer.stop()
            self._is_auto_scrolling = False
            self._waiting_to_next_chapter = False  # 重置等待标志
            self._pending_resume_after_chapter = False  # 重置待恢复标志
            self.auto_scroll_btn.setChecked(False)
            self.auto_scroll_btn.setText("📜 自动滚动")


# ==================== 阅读统计对话框 ====================

class ReadingStatsDialog(QDialog):
    """阅读统计对话框"""

    def __init__(self, book_id: int, reader_widget=None, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self.reader_widget = reader_widget  # 保存 reader_widget 引用
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

        # 计算总字数（累加所有章节字数）
        total_word_count = sum(ch.get('word_count', 0) for ch in chapters) if chapters else 0

        # 格式化字数显示：超过10万显示为"x万"
        if total_word_count >= 100000:
            word_count_str = f"{total_word_count / 10000:.1f} 万字"
        else:
            word_count_str = f"{total_word_count} 字"

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

        # 加上当前会话未保存的阅读时长（确保累计时间包含当前会话）
        if self.reader_widget and self.reader_widget.current_book_id == self.book_id:
            total_reading_seconds += self.reader_widget._unsaved_seconds

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
            f"{total_reading_seconds} 秒"
        )
        stats_grid.addLayout(time_item)

        # 总字数
        word_count_item = self._create_stat_item(
            "📖 总字数",
            word_count_str,
            ""
        )
        stats_grid.addLayout(word_count_item)

        # 总段数
        # chunks_item = self._create_stat_item(
        #     "📄 总段数",
        #     f"{chunk_count} 段",
        #     ""
        # )
        # stats_grid.addLayout(chunks_item)

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


# ==================== 自动滚动设置对话框 ====================

class AutoScrollSettingsDialog(QDialog):
    """自动滚动设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.setWindowTitle("⚙️ 自动滚动设置")
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("📜 自动滚动设置")
        title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #212529;")
        layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 创建设置表单
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # 1. 滚动速度
        speed_item = self._create_setting_item(
            "🚀 滚动速度",
            "控制文本滚动的速度",
            "reader_auto_scroll_speed",
            100,  # min
            3000,  # max
            100,   # step
            "ms",
            "滚动间隔（毫秒），越小越快"
        )
        form_layout.addLayout(speed_item)

        # 2. 自动切换下一章
        auto_next_item = self._create_checkbox_item(
            "📖 自动切换下一章",
            "滚动到底部时自动切换到下一章",
            "reader_auto_scroll_next_chapter",
            "启用后会自动切换到下一章并继续滚动"
        )
        form_layout.addLayout(auto_next_item)

        # 3. 底部停留时间
        switch_delay_item = self._create_setting_item(
            "⏸️ 章节底部停留",
            "在切换到下一章前的停留时间",
            "reader_chapter_switch_delay",
            0,      # min
            10000,  # max
            500,    # step
            "ms",
            "在章节底部停留的时间，用于消化内容"
        )
        form_layout.addLayout(switch_delay_item)

        # 4. 新章节准备时间
        start_delay_item = self._create_setting_item(
            "✨ 新章节准备",
            "切换到下一章后的准备时间",
            "reader_chapter_start_delay",
            0,      # min
            10000,  # max
            500,    # step
            "ms",
            "开始滚动前的准备时间，用于阅读章节标题"
        )
        form_layout.addLayout(start_delay_item)

        layout.addLayout(form_layout)

        # 预设配置
        preset_label = QLabel("💡 快速预设:")
        preset_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #495057;")
        layout.addWidget(preset_label)

        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)

        fast_btn = QPushButton("快速阅读")
        fast_btn.setStyleSheet(self._get_preset_button_style())
        fast_btn.clicked.connect(lambda: self._apply_preset("fast"))
        preset_layout.addWidget(fast_btn)

        normal_btn = QPushButton("正常节奏")
        normal_btn.setStyleSheet(self._get_preset_button_style())
        normal_btn.clicked.connect(lambda: self._apply_preset("normal"))
        preset_layout.addWidget(normal_btn)

        careful_btn = QPushButton("仔细阅读")
        careful_btn.setStyleSheet(self._get_preset_button_style())
        careful_btn.clicked.connect(lambda: self._apply_preset("careful"))
        preset_layout.addWidget(careful_btn)

        layout.addLayout(preset_layout)

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

    def _create_setting_item(self, title: str, description: str, config_key: str,
                            min_val: int, max_val: int, step: int,
                            suffix: str, tooltip: str):
        """创建设置项布局"""
        from novel_reader.core import settings as settings_module

        item_layout = QVBoxLayout()
        item_layout.setSpacing(5)

        # 标题和描述
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #212529;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        item_layout.addLayout(header_layout)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        item_layout.addWidget(desc_label)

        # 控制行
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 0, 0, 0)

        # SpinBox
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        current_value = settings_module.get_setting(config_key, 1000)
        spinbox.setValue(current_value)
        spinbox.setSuffix(f" {suffix}")
        spinbox.setSingleStep(step)
        spinbox.setStyleSheet("width: 120px;")
        spinbox.setToolTip(tooltip)

        # 保存控件引用，以便应用预设时使用
        setattr(self, f"_{config_key}_spinbox", spinbox)

        control_layout.addWidget(spinbox)
        control_layout.addStretch()

        # 值改变时更新父控件和保存配置
        spinbox.valueChanged.connect(
            lambda v, key=config_key: self._on_setting_changed(key, v)
        )

        item_layout.addLayout(control_layout)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e9ecef;")
        item_layout.addWidget(separator)

        return item_layout

    def _create_checkbox_item(self, title: str, description: str,
                              config_key: str, tooltip: str):
        """创建复选框设置项"""
        from novel_reader.core import settings as settings_module

        item_layout = QVBoxLayout()
        item_layout.setSpacing(5)

        # 标题和复选框
        header_layout = QHBoxLayout()

        checkbox = QCheckBox(title)
        current_value = settings_module.get_setting(config_key, True)
        checkbox.setChecked(current_value)
        checkbox.setStyleSheet("font-size: 13px; font-weight: bold; color: #212529;")
        checkbox.setToolTip(tooltip)

        # 保存控件引用
        setattr(self, f"_{config_key}_checkbox", checkbox)

        header_layout.addWidget(checkbox)
        header_layout.addStretch()
        item_layout.addLayout(header_layout)

        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        item_layout.addWidget(desc_label)

        # 值改变时更新父控件和保存配置
        checkbox.stateChanged.connect(
            lambda state, key=config_key: self._on_checkbox_changed(key, state)
        )

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e9ecef;")
        item_layout.addWidget(separator)

        return item_layout

    def _get_preset_button_style(self):
        """获取预设按钮样式"""
        return """
            QPushButton {
                padding: 6px 12px;
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
        """

    def _on_setting_changed(self, key: str, value: int):
        """设置值改变"""
        from novel_reader.core import settings as settings_module
        settings_module.set_setting(key, value)

        # 更新父控件
        if self.parent_widget:
            if key == "reader_auto_scroll_speed":
                self.parent_widget._scroll_speed = value
            elif key == "reader_chapter_switch_delay":
                self.parent_widget._chapter_switch_delay = value
            elif key == "reader_chapter_start_delay":
                self.parent_widget._chapter_start_delay = value

    def _on_checkbox_changed(self, key: str, state: int):
        """复选框值改变"""
        from PySide6.QtCore import Qt
        from novel_reader.core import settings as settings_module

        is_checked = (state == Qt.CheckState.Checked.value)
        settings_module.set_setting(key, is_checked)

        # 更新父控件
        if self.parent_widget and key == "reader_auto_scroll_next_chapter":
            self.parent_widget._auto_scroll_next_chapter = is_checked

    def _apply_preset(self, preset: str):
        """应用预设配置"""
        from novel_reader.core import settings as settings_module

        presets = {
            "fast": {
                "reader_auto_scroll_speed": 750,
                "reader_chapter_switch_delay": 3000,
                "reader_chapter_start_delay": 5000,
            },
            "normal": {
                "reader_auto_scroll_speed": 1000,
                "reader_chapter_switch_delay": 4000,
                "reader_chapter_start_delay": 7000,
            },
            "careful": {
                "reader_auto_scroll_speed": 1500,
                "reader_chapter_switch_delay": 5000,
                "reader_chapter_start_delay": 9000,
            }
        }

        if preset not in presets:
            return

        config = presets[preset]

        # 更新配置
        for key, value in config.items():
            settings_module.set_setting(key, value)
            self._on_setting_changed(key, value)

        # 更新控件显示
        self._reader_auto_scroll_speed_spinbox.setValue(config["reader_auto_scroll_speed"])
        self._reader_chapter_switch_delay_spinbox.setValue(config["reader_chapter_switch_delay"])
        self._reader_chapter_start_delay_spinbox.setValue(config["reader_chapter_start_delay"])

        print(f"[INFO] 已应用预设配置: {preset}")


# ==================== 切换书籍对话框 ====================

class SwitchBookDialog(QDialog):
    """切换书籍对话框"""

    def __init__(self, current_book_id: int, parent=None):
        super().__init__(parent)
        self.current_book_id = current_book_id
        self.selected_book_id = None
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        from novel_reader.core import list_books, get_book_chapters

        self.setWindowTitle("📚 切换书籍")
        self.setMinimumWidth(500)
        self.setMaximumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("📚 选择要阅读的书籍")
        title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #212529;")
        layout.addWidget(title_label)

        # 说明文本
        hint_label = QLabel("选择一本书籍即可切换，当前阅读进度会自动保存")
        hint_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        layout.addWidget(hint_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 书籍列表
        self.books_list = QListWidget()
        self.books_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                border: 1px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item[current] {
                border: 1px solid #007bff;
            }
        """)
        layout.addWidget(self.books_list)

        # 加载书籍列表
        books = list_books()
        if not books:
            self.books_list.addItem("暂无书籍")
        else:
            for book in books:
                book_id = book['id']
                title = book['title']

                # 获取章节数
                chapters = get_book_chapters(book_id)
                total_chapters = len(chapters) if chapters else 0

                # 格式化进度信息
                current_chapter = book.get('current_chapter', 0)
                if total_chapters > 0:
                    progress_text = f"{current_chapter}/{total_chapters}章"
                else:
                    progress_text = "未分章"

                # 标记当前书籍
                current_mark = " [当前]" if book_id == self.current_book_id else ""

                # 创建列表项
                item_text = f"{title}{current_mark}\n进度: {progress_text}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, book_id)

                # 当前书籍高亮显示
                if book_id == self.current_book_id:
                    item.setBackground(QColor("#e3f2fd"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.books_list.addItem(item)

        # 双击选择
        self.books_list.itemDoubleClicked.connect(self._accept_selection)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("确定")
        confirm_btn.setStyleSheet("""
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
        confirm_btn.clicked.connect(self._accept_selection)
        button_layout.addWidget(confirm_btn)

        layout.addLayout(button_layout)

    def _accept_selection(self):
        """确认选择"""
        current_item = self.books_list.currentItem()
        if current_item:
            self.selected_book_id = current_item.data(Qt.UserRole)
            # 如果选择的是当前书籍，不切换
            if self.selected_book_id == self.current_book_id:
                self.reject()
                return
            self.accept()
        else:
            self.reject()
