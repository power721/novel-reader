"""
主窗口 - Novel Reader 主界面 (使用新架构)
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QMessageBox, QFileDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Slot, QTimer
from typing import Optional

from .widgets import (
    BookListWidget,
    ChapterListWidget,
    BookmarkListWidget,
    PlayerWidget,
    TTSWidget
)
from .controllers import PlaybackControllerAdapter
from .dialogs import AboutDialog


class MainWindow(QMainWindow):
    """主窗口 (新架构)"""

    def __init__(self):
        super().__init__()

        # 状态变量
        self.current_book_id: Optional[int] = None
        self.playback_adapter: Optional[PlaybackControllerAdapter] = None

        # 初始化界面
        self._init_ui()
        self._connect_signals()

        # 初始化播放控制器
        self._init_playback_controller()

        # 加载数据
        self._load_data()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("Novel Reader - 有声书阅读器 (PySide6 + 新架构)")
        self.setGeometry(100, 100, 1400, 850)

        # 创建菜单栏
        self._create_menu_bar()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ==================== 三栏列表区域 ====================
        lists_splitter = QSplitter(Qt.Horizontal)

        # 左侧：书籍列表
        self.book_list_widget = BookListWidget()
        lists_splitter.addWidget(self.book_list_widget)

        # 中间：章节列表
        self.chapter_list_widget = ChapterListWidget()
        lists_splitter.addWidget(self.chapter_list_widget)

        # 右侧：书签列表
        self.bookmark_list_widget = BookmarkListWidget()
        lists_splitter.addWidget(self.bookmark_list_widget)

        # 设置拉伸比例
        lists_splitter.setStretchFactor(0, 1)
        lists_splitter.setStretchFactor(1, 1)
        lists_splitter.setStretchFactor(2, 1)

        main_layout.addWidget(lists_splitter)

        # ==================== 底部控制区域 ====================
        bottom_splitter = QSplitter(Qt.Horizontal)

        # TTS 转换组件
        self.tts_widget = TTSWidget()
        bottom_splitter.addWidget(self.tts_widget)

        # 播放控制组件
        self.player_widget = PlayerWidget()
        bottom_splitter.addWidget(self.player_widget)

        # 设置拉伸比例
        bottom_splitter.setStretchFactor(0, 2)
        bottom_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(bottom_splitter)

        # ==================== 底部状态栏 ====================
        self.statusBar().showMessage("就绪")

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入书籍...(&I)", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_book)
        file_menu.addAction(import_action)

        refresh_action = QAction("刷新列表(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")

        # 自动播放选项
        from novel_reader.core import get_setting
        auto_play_enabled = get_setting("auto_play_on_startup", True)
        auto_play_next_chapter_enabled = get_setting("auto_play_next_chapter", True)
        auto_play_next_book_enabled = get_setting("auto_play_next_book", False)

        self.auto_play_action = QAction("启动时自动播放(&A)", self)
        self.auto_play_action.setCheckable(True)
        self.auto_play_action.setChecked(auto_play_enabled)
        self.auto_play_action.triggered.connect(self._toggle_auto_play)
        settings_menu.addAction(self.auto_play_action)

        self.auto_play_next_chapter_action = QAction("自动播放下一章节(&C)", self)
        self.auto_play_next_chapter_action.setCheckable(True)
        self.auto_play_next_chapter_action.setChecked(auto_play_next_chapter_enabled)
        self.auto_play_next_chapter_action.triggered.connect(self._toggle_auto_play_next_chapter)
        settings_menu.addAction(self.auto_play_next_chapter_action)

        self.auto_play_next_book_action = QAction("自动播放下一本书(&N)", self)
        self.auto_play_next_book_action.setCheckable(True)
        self.auto_play_next_book_action.setChecked(auto_play_next_book_enabled)
        self.auto_play_next_book_action.triggered.connect(self._toggle_auto_play_next_book)
        settings_menu.addAction(self.auto_play_next_book_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        diagnose_action = QAction("诊断音频文件(&D)", self)
        diagnose_action.triggered.connect(self._diagnose_audio)
        help_menu.addAction(diagnose_action)

        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_playback_controller(self):
        """初始化播放控制器"""
        self.playback_adapter = PlaybackControllerAdapter(self)
        self.playback_adapter.initialize()

        # 连接信号
        self.playback_adapter.state_changed.connect(self._on_playback_state_changed)
        self.playback_adapter.chunk_changed.connect(self._on_chunk_changed)
        self.playback_adapter.chapter_changed.connect(self._on_chapter_changed)
        self.playback_adapter.progress_updated.connect(self._on_progress_updated)
        self.playback_adapter.book_finished.connect(self._on_book_finished)

    def _connect_signals(self):
        """连接信号和槽"""
        # 书籍列表信号
        self.book_list_widget.book_selected.connect(self._on_book_selected)
        self.book_list_widget.book_double_clicked.connect(self._on_book_double_clicked)
        self.book_list_widget.books_updated.connect(self._on_books_updated)
        self.book_list_widget.book_delete_requested.connect(self._on_delete_book)
        self.book_list_widget.book_rename_requested.connect(self._on_rename_book)

        # 章节列表信号
        self.chapter_list_widget.chapter_selected.connect(self._on_chapter_selected)
        self.chapter_list_widget.chapter_double_clicked.connect(self._on_chapter_double_clicked)

        # 书签列表信号
        self.bookmark_list_widget.bookmark_double_clicked.connect(self._on_bookmark_double_clicked)

        # 播放控制信号
        self.player_widget.play_requested.connect(self._play_book)
        self.player_widget.pause_requested.connect(self._pause_playback)
        self.player_widget.resume_requested.connect(self._resume_playback)
        self.player_widget.stop_requested.connect(self._stop_playback)
        self.player_widget.play_previous_chapter_requested.connect(self._play_previous_chapter)
        self.player_widget.play_next_chapter_requested.connect(self._play_next_chapter)
        self.player_widget.play_previous_chunk_requested.connect(self._play_previous_chunk)
        self.player_widget.play_next_chunk_requested.connect(self._play_next_chunk)

    def _load_data(self):
        """加载数据"""
        from novel_reader.core import list_books, get_setting

        # 获取最后播放的书籍ID
        last_book_id = get_setting("last_book_id", None)

        # 加载书籍列表，并自动选中上次播放的书
        if last_book_id:
            try:
                last_book_id = int(last_book_id)
            except (ValueError, TypeError):
                last_book_id = None

        self.book_list_widget.load_books(auto_select_book_id=last_book_id)

        # 获取当前选中的书籍
        books = list_books()
        if books:
            # 获取选中的书籍（如果有）
            selected_book_id = self.book_list_widget.get_selected_book_id()

            if selected_book_id:
                self.current_book_id = selected_book_id
                self.chapter_list_widget.load_chapters(selected_book_id)
                self.bookmark_list_widget.load_bookmarks(selected_book_id)
                self.player_widget.set_book(selected_book_id)
                self.tts_widget.set_book(selected_book_id)

                # 检查是否启用自动播放
                auto_play = get_setting("auto_play_on_startup", True)
                if auto_play:
                    # 延迟一点再自动播放，避免界面未完全加载
                    QTimer.singleShot(500, self._auto_play_last_position)

        self.statusBar().showMessage("数据已加载", 3000)

    def _auto_play_last_position(self):
        """自动播放上次的位置"""
        if not self.current_book_id:
            return

        # 检查是否已在播放
        if self.playback_adapter.is_playing:
            print("[DEBUG] Already playing, skipping auto-play")
            return

        # 获取当前书籍的播放进度
        from novel_reader.core import get_book
        book = get_book(self.current_book_id)
        if not book:
            return

        current_chunk = book['current_chunk']

        # 检查当前位置是否有音频
        from novel_reader.core.tts import AUDIO_DIR, chunk_to_audio_path
        audio_path = chunk_to_audio_path(self.current_book_id, current_chunk)

        from pathlib import Path
        if not Path(audio_path).exists():
            print(f"[DEBUG] Current chunk {current_chunk} audio not found, skipping auto-play")
            return

        # 开始播放
        print(f"[INFO] Auto-playing from last position: chunk {current_chunk}")
        self.statusBar().showMessage(f"继续播放: chunk {current_chunk}", 3000)
        self._load_and_play_from_chunk(current_chunk)

    # ==================== 播放控制器回调 ====================

    @Slot(str)
    def _on_playback_state_changed(self, state: str):
        """播放状态变化"""
        print(f"[DEBUG] State changed: {state}")

        if state == "PLAYING":
            self.player_widget.set_playing_state(True)
        elif state == "PAUSED":
            self.player_widget.set_paused_state(True)
        elif state == "STOPPED":
            self.player_widget.set_playing_state(False)

    @Slot(int)
    def _on_chunk_changed(self, chunk_id: int):
        """chunk变化"""
        # 更新数据库记录
        from novel_reader.core import update_book_progress
        update_book_progress(self.current_book_id, chunk_id)
        print(f"[DEBUG] Chunk changed: {chunk_id}")

    @Slot(int, str)
    def _on_chapter_changed(self, chapter_id: int, chapter_title: str):
        """章节变化"""
        self.chapter_list_widget.highlight_current_chapter_by_id(chapter_id)

        # 更新播放信息显示
        from novel_reader.core import get_book
        book = get_book(self.current_book_id)
        if book:
            book_title = book['title']
            self.player_widget.update_current_playback(book_title, chapter_title)

        self.statusBar().showMessage(f"📖 {chapter_title}", 3000)
        print(f"[DEBUG] Chapter changed: {chapter_id} - {chapter_title}")

    @Slot(int, int)
    def _on_progress_updated(self, current_ms: int, total_ms: int):
        """进度更新"""
        # 这里需要将毫秒转换为chunk索引
        from novel_reader.core import get_book
        book = get_book(self.current_book_id)
        if book:
            # 假设平均每个chunk 100字，每字约50ms
            chunk_id = current_ms // 5000  # 粗略估算
            self.player_widget.set_progress(chunk_id, book.get('total_chunks', 0))

    @Slot()
    def _on_book_finished(self):
        """书籍播放完成"""
        self.player_widget.set_playing_state(False)
        self.statusBar().showMessage("📚 播放完成", 3000)

        # 检查是否启用自动播放下一本书
        from novel_reader.core import get_setting, list_books
        auto_play_next_book = get_setting("auto_play_next_book", False)

        if auto_play_next_book and self.current_book_id:
            books = list_books()
            if not books:
                return

            # 查找当前书籍在列表中的位置
            current_index = -1
            for i, book in enumerate(books):
                if book['id'] == self.current_book_id:
                    current_index = i
                    break

            # 如果找到下一本书，自动播放
            if current_index >= 0 and current_index + 1 < len(books):
                next_book = books[current_index + 1]
                self.statusBar().showMessage(f"自动播放下一本书: {next_book['title']}", 3000)
                print(f"[INFO] Auto-playing next book: {next_book['title']}")

                # 切换到下一本书并开始播放
                self.current_book_id = next_book['id']
                self.chapter_list_widget.load_chapters(next_book['id'])
                self.bookmark_list_widget.load_bookmarks(next_book['id'])
                self.player_widget.set_book(next_book['id'])
                self.tts_widget.set_book(next_book['id'])

                # 延迟一点再开始播放
                QTimer.singleShot(500, lambda: self._play_book(next_book['id']))

    # ==================== 书籍相关槽函数 ====================

    @Slot(int)
    def _on_book_selected(self, book_id: int):
        """书籍被选中"""
        self.current_book_id = book_id

        # 更新子组件状态
        self.chapter_list_widget.load_chapters(book_id)
        self.bookmark_list_widget.load_bookmarks(book_id)
        self.player_widget.set_book(book_id)
        self.tts_widget.set_book(book_id)

        # 显示播放历史记录
        from novel_reader.core import get_book, get_book_chapters
        book = get_book(book_id)
        if book:
            current_chapter = book.get('current_chapter', 0)
            current_chunk = book.get('current_chunk', 0)
            last_played_at = book.get('last_played_at')

            chapters = get_book_chapters(book_id)
            total_chapters = len(chapters)

            # 找到当前章节的标题
            chapter_title = ""
            if total_chapters > 0 and current_chapter > 0 and current_chapter <= total_chapters:
                chapter_title = chapters[current_chapter - 1]['title']

            if last_played_at:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_played_at)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = last_played_at
            else:
                time_str = "未播放"

            if chapter_title:
                status_msg = f"《{book['title']}》 - 上次播放: 第{current_chapter}章 {chapter_title} (chunk {current_chunk}) - {time_str}"
            else:
                status_msg = f"《{book['title']}》 - 上次播放: chunk {current_chunk} - {time_str}"

            self.statusBar().showMessage(status_msg, 5000)
        else:
            self.statusBar().showMessage(f"已选择书籍 ID: {book_id}", 3000)

    @Slot(int)
    def _on_book_double_clicked(self, book_id: int):
        """书籍被双击 - 加载并播放"""
        from novel_reader.core import get_book
        book = get_book(book_id)
        if book:
            self._load_and_play_from_chunk(book['current_chunk'])

    @Slot()
    def _on_books_updated(self):
        """书籍列表更新"""
        from novel_reader.core import list_books
        books = list_books()
        self.statusBar().showMessage(f"共 {len(books)} 本书", 3000)

    def _import_book(self):
        """导入书籍"""
        self.book_list_widget.import_book_dialog()

    def _toggle_auto_play(self):
        """切换自动播放设置"""
        from novel_reader.core import set_setting
        current_state = self.auto_play_action.isChecked()
        set_setting("auto_play_on_startup", current_state)
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}启动时自动播放", 3000)
        print(f"[INFO] Auto-play on startup: {status}")

    def _toggle_auto_play_next_book(self):
        """切换自动播放下一本书设置"""
        from novel_reader.core import set_setting
        current_state = self.auto_play_next_book_action.isChecked()
        set_setting("auto_play_next_book", current_state)
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}自动播放下一本书", 3000)
        print(f"[INFO] Auto-play next book: {status}")

    def _toggle_auto_play_next_chapter(self):
        """切换自动播放下一章节设置"""
        from novel_reader.core import set_setting
        current_state = self.auto_play_next_chapter_action.isChecked()
        set_setting("auto_play_next_chapter", current_state)
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}自动播放下一章节", 3000)
        print(f"[INFO] Auto-play next chapter: {status}")

    @Slot(int)
    def _on_delete_book(self, book_id: int):
        """删除书籍"""
        # 检查是否正在播放该书
        if self.playback_adapter.is_playing and self.current_book_id == book_id:
            QMessageBox.warning(
                self,
                "无法删除",
                "该书籍正在播放中，请先停止播放"
            )
            return

        # 获取书籍信息
        from novel_reader.core import get_book
        book = get_book(book_id)
        if not book:
            QMessageBox.warning(self, "错误", "书籍不存在")
            return

        # 删除书籍
        from novel_reader.core import delete_book
        success = delete_book(book_id, delete_audio=True)

        if success:
            # 如果删除的是当前选中的书，清空UI
            if self.current_book_id == book_id:
                self.current_book_id = None
                self.chapter_list_widget.clear()
                self.bookmark_list_widget.clear()
                self.player_widget.reset()
                self.tts_widget.clear_log()

            # 刷新书籍列表
            self.book_list_widget.load_books()

            QMessageBox.information(
                self,
                "删除成功",
                f"已删除书籍：《{book['title']}》"
            )
            self.statusBar().showMessage("书籍已删除", 3000)
        else:
            QMessageBox.critical(self, "错误", "删除失败")

    @Slot(int, str)
    def _on_rename_book(self, book_id: int, current_title: str):
        """重命名书籍"""
        # 显示重命名对话框
        from .dialogs import rename_book_dialog
        new_title = rename_book_dialog(self, current_title)

        if not new_title:
            # 用户取消或书名未改变
            return

        # 更新书名
        from novel_reader.core import update_book_title
        success = update_book_title(book_id, new_title)

        if success:
            # 刷新书籍列表
            self.book_list_widget.load_books()

            # 如果重命名的是当前选中的书，更新状态栏
            if self.current_book_id == book_id:
                self.statusBar().showMessage(f"已重命名: 《{new_title}》", 3000)

            QMessageBox.information(
                self,
                "重命名成功",
                f"书名已更新:\n\n{current_title} → {new_title}"
            )
        else:
            QMessageBox.critical(self, "错误", "重命名失败")

    # ==================== 播放相关槽函数 ====================

    @Slot(int)
    def _play_book(self, book_id: int):
        """播放书籍"""
        print(f"[DEBUG] _play_book called: book_id={book_id}")

        if self.playback_adapter.is_playing:
            print("[DEBUG] Already playing, returning")
            QMessageBox.information(self, "提示", "正在播放中，请先停止")
            return

        # 保存最后播放的书籍ID
        from novel_reader.core import set_setting
        set_setting("last_book_id", book_id)

        from novel_reader.core import get_book
        book = get_book(book_id)
        if book:
            self._load_and_play_from_chunk(book['current_chunk'])

    def _load_and_play_from_chunk(self, chunk_id: int):
        """加载书籍并从指定位置播放"""
        from novel_reader.core import get_book

        book = get_book(self.current_book_id)
        if not book:
            return

        # 停止当前播放
        self._stop_playback()

        # 加载书籍到控制器
        try:
            loaded_book = self.playback_adapter.load_book(
                self.current_book_id,
                book['file_path']
            )

            # 获取当前章节标题
            current_chapter = self.playback_adapter.current_chapter
            if current_chapter:
                self.player_widget.update_current_playback(
                    book['title'],
                    current_chapter.title
                )
            else:
                self.player_widget.update_current_playback(book['title'], "")

            # 跳转到指定chunk
            self.playback_adapter.seek_to_chunk(chunk_id)

            # 开始播放
            self.playback_adapter.play()

            self.statusBar().showMessage(f"正在播放书籍 ID: {self.current_book_id}")

        except Exception as e:
            QMessageBox.critical(self, "播放错误", f"加载书籍失败: {str(e)}")
            print(f"[ERROR] Failed to load book: {e}")

    @Slot()
    def _pause_playback(self):
        """暂停播放"""
        self.playback_adapter.pause()
        self.statusBar().showMessage("已暂停", 3000)

    @Slot()
    def _resume_playback(self):
        """恢复播放"""
        self.playback_adapter.resume()
        self.statusBar().showMessage("继续播放", 3000)

    @Slot()
    def _stop_playback(self):
        """停止播放"""
        self.playback_adapter.stop()
        self.player_widget.set_playing_state(False)
        self.statusBar().showMessage("播放已停止", 3000)

    def _play_previous_chapter(self):
        """播放上一章"""
        self.playback_adapter.prev_chapter()

    def _play_next_chapter(self):
        """播放下一章"""
        self.playback_adapter.next_chapter()

    def _play_next_chunk(self):
        """播放下一个分段"""
        if not self.playback_adapter.current_book:
            QMessageBox.warning(self, "警告", "请先加载一本书")
            return

        from novel_reader.core import get_book
        from novel_reader.utils import load_txt_file, parse_txt

        book = get_book(self.current_book_id)
        if not book:
            return

        # 获取当前chunk
        current_chunk = book['current_chunk']

        # 获取总chunk数
        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)
        total_chunks = len(chunks)

        # 计算下一个chunk
        next_chunk = current_chunk + 1

        if next_chunk >= total_chunks:
            QMessageBox.information(self, "提示", "已经是最后一个分段了")
            return

        # 跳转到下一个chunk
        self.playback_adapter.seek_to_chunk(next_chunk)

        # 如果未播放，开始播放
        if not self.playback_adapter.is_playing:
            self.playback_adapter.play()

        self.statusBar().showMessage(f"跳转到分段 {next_chunk}", 3000)

    def _play_previous_chunk(self):
        """播放上一个分段"""
        if not self.playback_adapter.current_book:
            QMessageBox.warning(self, "警告", "请先加载一本书")
            return

        from novel_reader.core import get_book

        book = get_book(self.current_book_id)
        if not book:
            return

        # 获取当前chunk
        current_chunk = book['current_chunk']

        # 计算上一个chunk
        prev_chunk = current_chunk - 1

        if prev_chunk < 0:
            QMessageBox.information(self, "提示", "已经是第一个分段了")
            return

        # 跳转到上一个chunk
        self.playback_adapter.seek_to_chunk(prev_chunk)

        # 如果未播放，开始播放
        if not self.playback_adapter.is_playing:
            self.playback_adapter.play()

        self.statusBar().showMessage(f"跳转到分段 {prev_chunk}", 3000)

    # ==================== 章节相关槽函数 ====================

    @Slot(int)
    def _on_chapter_selected(self, start_chunk: int):
        """章节被选中"""
        print(f"[DEBUG] Chapter selected: start_chunk={start_chunk}")
        # TODO: 实现章节选中逻辑

    @Slot(int)
    def _on_chapter_double_clicked(self, start_chunk: int):
        """章节被双击 - 强制从指定位置播放"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        # 停止当前播放
        self._stop_playback()

        # 从指定位置开始播放
        self._load_and_play_from_chunk(start_chunk)

    @Slot(int)
    def _on_bookmark_double_clicked(self, chunk: int):
        """书签被双击"""
        self._on_chapter_double_clicked(chunk)

    # ==================== 辅助方法 ====================

    def _refresh_all(self):
        """刷新所有数据"""
        self._load_data()
        if self.current_book_id:
            self.chapter_list_widget.load_chapters(self.current_book_id)
            self.bookmark_list_widget.load_bookmarks(self.current_book_id)
        self.statusBar().showMessage("已刷新", 3000)

    def _diagnose_audio(self):
        """诊断当前书籍的音频文件"""
        if not self.current_book_id:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core.player import diagnose_audio_files, print_diagnosis, delete_corrupted_audio

        # 诊断音频文件
        diagnosis = diagnose_audio_files(self.current_book_id)

        # 显示诊断结果
        print_diagnosis(diagnosis)

        # 如果有问题，询问是否删除
        if diagnosis.get('problematic', 0) > 0:
            reply = QMessageBox.question(
                self,
                "发现问题",
                f"发现 {diagnosis['problematic']} 个问题文件\n\n"
                f"缺失: {diagnosis['missing']}\n"
                f"空文件: {diagnosis['empty']}\n"
                f"过小 (<20KB): {diagnosis['too_small']}\n\n"
                f"是否删除空文件和过小的文件？\n"
                f"(删除后需要重新转换)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                deleted = delete_corrupted_audio(self.current_book_id, diagnosis)
                QMessageBox.information(
                    self,
                    "删除完成",
                    f"已删除 {deleted} 个损坏的文件 (<20KB)\n\n请重新转换这些章节"
                )
                # 刷新书籍列表
                self.book_list_widget.load_books()
        else:
            QMessageBox.information(
                self,
                "诊断完成",
                "✅ 所有音频文件正常！"
            )

    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    # ==================== 窗口事件 ====================

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止播放
        if self.playback_adapter:
            self.playback_adapter.shutdown()

        event.accept()
