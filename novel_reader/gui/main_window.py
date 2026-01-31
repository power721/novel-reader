"""
主窗口 - Novel Reader 主界面
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QMessageBox, QFileDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Slot
from typing import Optional

from .widgets import (
    BookListWidget,
    ChapterListWidget,
    BookmarkListWidget,
    PlayerWidget,
    TTSWidget
)
from .workers import PlaybackWorker, TTSWorker
from .dialogs import AboutDialog


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 状态变量
        self.current_book_id: Optional[int] = None
        self.playback_worker: Optional[PlaybackWorker] = None
        self.tts_worker: Optional[TTSWorker] = None

        # 初始化界面
        self._init_ui()
        self._connect_signals()

        # 加载数据
        self._load_data()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("Novel Reader - 有声书阅读器 (PySide6)")
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

        debug_chunk_action = QAction("调试当前Chunk(&C)", self)
        debug_chunk_action.triggered.connect(self._debug_current_chunk)
        help_menu.addAction(debug_chunk_action)

        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """连接信号和槽"""
        # 书籍列表信号
        self.book_list_widget.book_selected.connect(self._on_book_selected)
        self.book_list_widget.book_double_clicked.connect(self._on_book_double_clicked)
        self.book_list_widget.books_updated.connect(self._on_books_updated)
        self.book_list_widget.book_delete_requested.connect(self._on_delete_book)
        self.book_list_widget.book_rename_requested.connect(self._on_rename_book)
        self.book_list_widget.book_imported.connect(self._on_book_imported)

        # 章节列表信号
        self.chapter_list_widget.chapter_selected.connect(self._on_chapter_selected)
        self.chapter_list_widget.chapter_double_clicked.connect(self._on_chapter_double_clicked)

        # 书签列表信号
        self.bookmark_list_widget.bookmark_double_clicked.connect(self._on_bookmark_double_clicked)

        # 播放控制信号
        self.player_widget.play_requested.connect(self._play_book)
        self.player_widget.stop_requested.connect(self._stop_playback)
        self.player_widget.play_previous_chapter_requested.connect(self._play_previous_chapter)
        self.player_widget.play_next_chapter_requested.connect(self._play_next_chapter)
        self.player_widget.play_previous_chunk_requested.connect(self._play_previous_chunk)
        self.player_widget.play_next_chunk_requested.connect(self._play_next_chunk)

        # TTS 转换信号
        self.tts_widget.convert_book_requested.connect(self._convert_book)

    def _load_data(self):
        """加载数据"""
        from novel_reader.core import list_books, get_setting, get_book

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
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(500, self._auto_play_last_position)

        self.statusBar().showMessage("数据已加载", 3000)

    def _auto_play_last_position(self):
        """自动播放上次的位置"""
        if not self.current_book_id:
            return

        # 检查是否已在播放
        if self.playback_worker and self.playback_worker.isRunning():
            print("[DEBUG] Already playing, skipping auto-play")
            return

        # 检查是否有音频文件
        has_audio, audio_count = self._check_audio_files(self.current_book_id)

        if not has_audio:
            print("[DEBUG] No audio files, skipping auto-play")
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
        self._play_from_chunk(current_chunk)

    def _refresh_all(self):
        """刷新所有数据"""
        self._load_data()
        if self.current_book_id:
            self.chapter_list_widget.load_chapters(self.current_book_id)
            self.bookmark_list_widget.load_bookmarks(self.current_book_id)
        self.statusBar().showMessage("已刷新", 3000)

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
        """书籍被双击 - 检查后播放或转换"""
        # 检查是否有音频文件
        has_audio, audio_count = self._check_audio_files(book_id)

        if not has_audio:
            # 没有音频文件，提示用户
            QMessageBox.information(
                self,
                "提示",
                "该书籍尚未进行 TTS 转换。\n\n"
                "请在章节列表中点击章节开始转换和播放。\n\n"
                "或点击「转换整本书」按钮进行批量转换。"
            )
            return

        # 有音频文件，检查当前进度
        from novel_reader.core import get_book
        book = get_book(book_id)
        current_chunk = book['current_chunk']

        self.statusBar().showMessage(f"准备播放从 chunk {current_chunk} 开始...")
        # 从当前进度开始播放
        self._play_book(book_id)

    @Slot()
    def _on_books_updated(self):
        """书籍列表更新"""
        # 更新状态栏
        from novel_reader.core import list_books
        books = list_books()
        self.statusBar().showMessage(f"共 {len(books)} 本书", 3000)

    def _import_book(self):
        """导入书籍"""
        self.book_list_widget.import_book_dialog()

    def _toggle_auto_play(self):
        """切换自动播放设置"""
        from novel_reader.core import set_setting, get_setting

        # 获取当前状态
        current_state = self.auto_play_action.isChecked()

        # 保存设置
        set_setting("auto_play_on_startup", current_state)

        # 显示提示
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}启动时自动播放", 3000)
        print(f"[INFO] Auto-play on startup: {status}")

    def _toggle_auto_play_next_book(self):
        """切换自动播放下一本书设置"""
        from novel_reader.core import set_setting, get_setting

        # 获取当前状态
        current_state = self.auto_play_next_book_action.isChecked()

        # 保存设置
        set_setting("auto_play_next_book", current_state)

        # 显示提示
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}自动播放下一本书", 3000)
        print(f"[INFO] Auto-play next book: {status}")

    def _toggle_auto_play_next_chapter(self):
        """切换自动播放下一章节设置"""
        from novel_reader.core import set_setting, get_setting

        # 获取当前状态
        current_state = self.auto_play_next_chapter_action.isChecked()

        # 保存设置
        set_setting("auto_play_next_chapter", current_state)

        # 显示提示
        status = "启用" if current_state else "禁用"
        self.statusBar().showMessage(f"已{status}自动播放下一章节", 3000)
        print(f"[INFO] Auto-play next chapter: {status}")

    @Slot(int)
    def _on_delete_book(self, book_id: int):
        """删除书籍"""
        # 检查是否正在播放或转换该书
        if (self.playback_worker and self.playback_worker.isRunning() and
            self.current_book_id == book_id):
            QMessageBox.warning(
                self,
                "无法删除",
                "该书籍正在播放中，请先停止播放"
            )
            return

        if (self.tts_worker and self.tts_worker.isRunning() and
            self.current_book_id == book_id):
            QMessageBox.warning(
                self,
                "无法删除",
                "该书籍正在转换中，请先停止转换"
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

    @Slot(int)
    def _on_book_imported(self, book_id: int):
        """书籍导入成功后自动转换前2个chunk"""
        print(f"[INFO] Book imported: {book_id}, starting auto-conversion of first 2 chunks")

        # 获取书籍信息
        from novel_reader.core import get_book
        from novel_reader.utils import load_txt_file, parse_txt

        book = get_book(book_id)
        if not book:
            return

        # 获取总chunk数
        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)
        total_chunks = len(chunks)

        # 确定要转换的chunk数量（前2个或全部）
        chunks_to_convert = min(2, total_chunks)

        print(f"[INFO] Auto-converting {chunks_to_convert} chunks (total: {total_chunks})")

        # 启动TTS转换（后台模式）
        self._auto_convert_first_chunks(book_id, chunks_to_convert)

    def _auto_convert_first_chunks(self, book_id: int, count: int):
        """
        自动转换前N个chunk

        Args:
            book_id: 书籍ID
            count: chunk数量
        """
        if self.tts_worker and self.tts_worker.isRunning():
            print("[DEBUG] TTS worker already running, skipping auto-conversion")
            return

        # 清空日志
        self.tts_widget.clear_log()
        self.tts_widget.set_converting_state(True)

        # 保存起始位置用于播放
        self._pending_play_chunk = 0
        self._conversion_in_progress = True

        # 创建TTS工作线程（前N个chunk）
        print(f"[DEBUG] Creating TTSWorker for first {count} chunks...")
        self.tts_worker = TTSWorker(
            book_id,
            start_chunk=0,
            end_chunk=count,  # 只转换前N个
            chapter_mode=False  # 不使用章节模式
        )
        print(f"[DEBUG] Connecting signals...")
        self.tts_worker.progress.connect(self._on_tts_progress)
        self.tts_worker.log.connect(self._on_tts_log)
        self.tts_worker.finished.connect(self._on_auto_convert_finished)
        self.tts_worker.error.connect(self._on_tts_error)
        print(f"[DEBUG] Starting TTS worker...")
        self.tts_worker.start()
        print(f"[DEBUG] TTS worker started")

        self.statusBar().showMessage(f"🔄 自动转换前{count}个分段...")

    @Slot()
    def _on_auto_convert_finished(self):
        """自动转换完成"""
        self.tts_widget.set_converting_state(False)
        self.statusBar().showMessage("✅ 前置分段转换完成，可以开始播放了", 5000)
        print("[INFO] Auto-conversion of first chunks completed")

    # ==================== 播放相关槽函数 ====================

    def _check_audio_files(self, book_id: int) -> tuple[bool, int]:
        """
        检查书籍是否有音频文件

        Returns:
            (has_audio, count): has_audio 表示是否有音频，count 表示音频数量
        """
        from pathlib import Path
        from novel_reader.core.tts import AUDIO_DIR

        book_audio_dir = AUDIO_DIR / str(book_id)

        if not book_audio_dir.exists():
            return False, 0

        # 统计音频文件数量
        audio_files = list(book_audio_dir.glob("*.wav"))
        return len(audio_files) > 0, len(audio_files)

    @Slot(int)
    def _play_book(self, book_id: int):
        """播放书籍"""
        print(f"[DEBUG] _play_book called: book_id={book_id}")

        if self.playback_worker and self.playback_worker.isRunning():
            print("[DEBUG] Already playing, returning")
            QMessageBox.information(self, "提示", "正在播放中，请先停止")
            return

        # 保存最后播放的书籍ID
        from novel_reader.core import set_setting
        set_setting("last_book_id", book_id)

        # 检查是否有音频文件
        has_audio, audio_count = self._check_audio_files(book_id)

        if not has_audio:
            reply = QMessageBox.question(
                self,
                "未找到音频文件",
                "该书籍尚未进行 TTS 转换。\n\n是否立即开始转换？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self._convert_book(book_id)
            return

        # 显示音频数量信息
        self.statusBar().showMessage(f"找到 {audio_count} 个音频文件，开始播放...")

        # 创建播放工作线程
        self.playback_worker = PlaybackWorker(book_id)
        self.playback_worker.finished.connect(self._on_playback_finished)
        self.playback_worker.error.connect(self._on_playback_error)
        self.playback_worker.progress_updated.connect(self._on_playback_progress)
        self.playback_worker.chapter_finished.connect(self._on_chapter_playback_finished)
        self.playback_worker.last_chunk_of_chapter_started.connect(self._on_last_chunk_of_chapter_started)
        self.playback_worker.start()

        # 获取书籍信息和当前章节，更新播放显示
        from novel_reader.core import get_book, get_book_chapters
        book = get_book(book_id)
        if book:
            # 获取当前章节
            chapters = get_book_chapters(book_id)
            current_chapter = book.get('current_chapter', 0)

            # 找到当前章节的标题
            chapter_title = ""
            if chapters and 0 <= current_chapter - 1 < len(chapters):
                chapter_title = chapters[current_chapter - 1]['title']

            # 更新播放显示
            self.player_widget.update_current_playback(book['title'], chapter_title)

        # 更新 UI 状态
        self.player_widget.set_playing_state(True)
        self.statusBar().showMessage(f"正在播放书籍 ID: {book_id}")

    @Slot()
    def _stop_playback(self):
        """停止播放"""
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        self.player_widget.set_playing_state(False)
        # self.book_list_widget.load_books()
        self.statusBar().showMessage("播放已停止", 3000)

    @Slot()
    def _on_playback_finished(self):
        """播放完成"""
        self.player_widget.set_playing_state(False)
        # self.book_list_widget.load_books()
        self.statusBar().showMessage("播放完成", 3000)

        # 检查是否启用自动播放下一本书
        from novel_reader.core import get_setting, list_books, get_book
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
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, lambda: self._play_book(next_book['id']))

    @Slot(str)
    def _on_playback_error(self, error_msg: str):
        """播放错误"""
        self.player_widget.set_playing_state(False)
        QMessageBox.critical(self, "播放错误", f"播放失败: {error_msg}")
        self.statusBar().showMessage("播放失败", 3000)

    @Slot(int, int)
    def _on_playback_progress(self, current: int, total: int):
        """播放进度更新"""
        self.player_widget.set_progress(current, total)
        # 高亮当前播放的章节
        self.chapter_list_widget.highlight_current_chapter(current)

        # 更新播放状态显示（获取当前章节标题）
        if self.current_book_id:
            from novel_reader.core import get_book, get_book_chapters
            book = get_book(self.current_book_id)
            if book:
                chapters = get_book_chapters(self.current_book_id)
                if chapters:
                    # 找到包含current chunk的章节
                    chapter_title = ""
                    for chapter in chapters:
                        chapter_start = chapter['start_chunk']
                        # 检查这个章节是否包含current chunk
                        # 简化处理：使用第一个匹配的章节
                        if chapter_start <= current:
                            chapter_title = chapter['title']
                        else:
                            break

                    # 更新播放显示
                    if chapter_title:
                        self.player_widget.update_current_playback(book['title'], chapter_title)
                        # 重新设置播放状态以更新显示文本
                        if self.player_widget.is_playing:
                            self.player_widget.set_playing_state(True)

    @Slot(int, int)
    def _on_chapter_playback_finished(self, current_chunk: int, next_chapter_start: int):
        """章节播放完成，自动播放下一章节"""
        from novel_reader.core import get_setting, get_book_chapters

        # 检查是否启用自动播放下一章节
        auto_play_next_chapter = get_setting("auto_play_next_chapter", True)
        if not auto_play_next_chapter:
            return

        # 检查下一章节的音频是否存在
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        next_chapter_audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{next_chapter_start:05d}.wav"

        if not Path(next_chapter_audio_path).exists():
            # 下一章节的音频不存在，需要转换
            chapters = get_book_chapters(self.current_book_id)
            # 找到下一章节的标题
            next_chapter_title = f"chunk {next_chapter_start}"
            for i, chapter in enumerate(chapters):
                if chapter['start_chunk'] == next_chapter_start:
                    next_chapter_title = chapter['title']
                    break
                elif i + 1 < len(chapters) and chapters[i + 1]['start_chunk'] == next_chapter_start:
                    next_chapter_title = chapters[i + 1]['title']
                    break

            print(f"🔄 下一章节音频未找到，开始 TTS 转换: {next_chapter_title} (从 chunk {next_chapter_start})")
            self.statusBar().showMessage(f"📖 章节播放完成，开始转换: {next_chapter_title}...")

            # 停止当前播放
            if self.playback_worker and self.playback_worker.isRunning():
                self.playback_worker.stop()
                self.playback_worker.wait()

            # 转换下一章节并播放
            self._convert_chapter_and_play(self.current_book_id, next_chapter_start)
        else:
            # 下一章节的音频已存在，播放会自动继续
            chapters = get_book_chapters(self.current_book_id)
            # 找到下一章节的标题
            next_chapter_title = f"chunk {next_chapter_start}"
            for i, chapter in enumerate(chapters):
                if chapter['start_chunk'] == next_chapter_start:
                    next_chapter_title = chapter['title']
                    break
                elif i + 1 < len(chapters) and chapters[i + 1]['start_chunk'] == next_chapter_start:
                    next_chapter_title = chapters[i + 1]['title']
                    break

            print(f"✅ 下一章节音频已存在，自动继续播放: {next_chapter_title}")
            self.statusBar().showMessage(f"📖 进入下一章节: {next_chapter_title}")

    @Slot(int)
    def _on_last_chunk_of_chapter_started(self, next_chapter_start: int):
        """章节最后一个chunk开始播放，提前转换下一章节"""
        from novel_reader.core import get_book_chapters, get_setting
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        # 检查是否启用自动播放下一章节
        auto_play_next_chapter = get_setting("auto_play_next_chapter", True)
        if not auto_play_next_chapter:
            return

        # 如果TTS worker已经在运行，不重复转换
        if self.tts_worker and self.tts_worker.isRunning():
            print(f"[DEBUG] TTS already running, skipping pre-conversion")
            return

        # 检查下一章节的音频是否存在
        next_chapter_audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{next_chapter_start:05d}.wav"

        if Path(next_chapter_audio_path).exists():
            # 文件存在，检查大小
            file_size = Path(next_chapter_audio_path).stat().st_size
            if file_size > 20000:  # 大于20KB认为有效
                print(f"✅ 下一章节音频已存在 ({file_size/1024:.1f} KB)，无需转换")
                return
            else:
                print(f"⚠ 下一章节音频文件过小 ({file_size} bytes)，需要重新转换")

        # 获取下一章节标题
        chapters = get_book_chapters(self.current_book_id)
        next_chapter_title = f"chunk {next_chapter_start}"
        for i, chapter in enumerate(chapters):
            if chapter['start_chunk'] == next_chapter_start:
                next_chapter_title = chapter['title']
                break
            elif i + 1 < len(chapters) and i + 1 < len(chapters) and chapters[i + 1]['start_chunk'] == next_chapter_start:
                next_chapter_title = chapters[i + 1]['title']
                break

        print(f"🔄 提前转换下一章节: {next_chapter_title} (从 chunk {next_chapter_start})")
        self.statusBar().showMessage(f"🔄 后台转换下一章节: {next_chapter_title}...")

        # 启动TTS转换（后台模式，不立即播放）
        self._start_background_tts(next_chapter_start, next_chapter_title)

    def _start_background_tts(self, start_chunk: int, chapter_title: str = ""):
        """
        启动后台TTS转换（不立即播放）

        Args:
            start_chunk: 起始 chunk ID
            chapter_title: 章节标题
        """
        if self.tts_worker and self.tts_worker.isRunning():
            print(f"[DEBUG] TTS worker already running, skipping")
            return

        # 清空日志
        self.tts_widget.clear_log()
        self.tts_widget.set_converting_state(True)

        # 创建TTS工作线程（章节模式，不连接first_chunk_ready信号以避免重复播放）
        print(f"[DEBUG] Creating background TTSWorker...")
        self.tts_worker = TTSWorker(self.current_book_id, start_chunk=start_chunk, chapter_mode=True)
        print(f"[DEBUG] Connecting signals...")
        self.tts_worker.progress.connect(self._on_tts_progress)
        self.tts_worker.log.connect(self._on_tts_log)
        # 不连接first_chunk_ready，避免在播放过程中重复启动播放
        self.tts_worker.chapter_finished.connect(self._on_chapter_tts_finished)
        self.tts_worker.finished.connect(self._on_tts_finished)
        self.tts_worker.error.connect(self._on_tts_error)
        print(f"[DEBUG] Starting background TTS worker...")
        self.tts_worker.start()
        print(f"[DEBUG] Background TTS worker started")

        title_msg = f"转换: {chapter_title}" if chapter_title else f"转换从 chunk {start_chunk} 开始"
        self.statusBar().showMessage(f"🔄 后台{title_msg}...")

    @Slot(int)
    def _on_chapter_selected(self, start_chunk: int):
        """章节被选中 - 转换当前章节并自动播放"""
        print(f"[DEBUG] _on_chapter_selected called: start_chunk={start_chunk}, current_book_id={self.current_book_id}")

        if self.current_book_id is None:
            print("[DEBUG] current_book_id is None, returning")
            return

        # 检查是否正在转换或播放
        if (self.tts_worker and self.tts_worker.isRunning()) or \
           (self.playback_worker and self.playback_worker.isRunning()):
            print("[DEBUG] Already converting or playing, returning")
            return  # 已在转换或播放中，不重复触发

        # 获取总 chunk 数
        from novel_reader.core import get_book
        from novel_reader.utils import load_txt_file, parse_txt
        book = get_book(self.current_book_id)
        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)
        total_chunks = len(chunks)

        # 找到包含 start_chunk 的章节
        from novel_reader.core import get_book_chapters
        book_chapters = get_book_chapters(self.current_book_id)

        print(f"[DEBUG] Found {len(book_chapters)} chapters, total chunks: {total_chunks}")

        # 找到包含 start_chunk 的章节的结束位置
        current_chapter_end = total_chunks  # 默认到文件末尾

        # 遍历章节，找到包含 start_chunk 的章节
        found_chapter_idx = None
        for i, chapter in enumerate(book_chapters):
            chapter_start = chapter['start_chunk']
            # 当前章节的开始位置 <= start_chunk < 下一章的开始位置
            if chapter_start <= start_chunk:
                # 检查是否是包含 start_chunk 的章节
                if i + 1 < len(book_chapters):
                    next_chapter_start_in_loop = book_chapters[i + 1]['start_chunk']
                    if start_chunk < next_chapter_start_in_loop:
                        found_chapter_idx = i
                        current_chapter_end = next_chapter_start_in_loop
                        break
                else:
                    # 最后一章
                    found_chapter_idx = i
                    current_chapter_end = total_chunks
                    break

        if found_chapter_idx is not None:
            print(f"[DEBUG] Found chapter at index {found_chapter_idx}: start={book_chapters[found_chapter_idx]['start_chunk']}, end={current_chapter_end}")

        print(f"[DEBUG] Chapter range: {start_chunk} - {current_chapter_end}")

        # 检查当前章节是否已转换（只检查到章节结束）
        chapter_has_audio = True
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        # 确保范围有效
        if start_chunk >= current_chapter_end:
            print(f"[DEBUG] Invalid range: {start_chunk} >= {current_chapter_end}")
            current_chapter_end = min(start_chunk + 1, total_chunks)

        for i in range(start_chunk, current_chapter_end):
            audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{i:05d}.wav"
            if not Path(audio_path).exists():
                chapter_has_audio = False
                print(f"[DEBUG] Missing audio for chunk {i}")
                break

        print(f"[DEBUG] Chapter has audio: {chapter_has_audio}")

        if chapter_has_audio:
            # 当前章节已转换，可以直接播放
            self.statusBar().showMessage(f"章节 chunk {start_chunk} 已转换，开始播放...")
            print("[DEBUG] Calling _play_from_chunk")
            self._play_from_chunk(start_chunk)
        else:
            # 当前章节未转换，开始转换并自动播放
            self.statusBar().showMessage(f"章节 chunk {start_chunk} 未转换，开始 TTS 转换...")
            print("[DEBUG] Calling _convert_chapter_and_play")
            self._convert_chapter_and_play(self.current_book_id, start_chunk)

    @Slot(int)
    def _on_chapter_double_clicked(self, start_chunk: int):
        """章节被双击 - 强制从指定位置播放或转换后播放"""
        print(f"[DEBUG] _on_chapter_double_clicked called: start_chunk={start_chunk}, current_book_id={self.current_book_id}")

        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        # 强制停止当前播放
        if self.playback_worker and self.playback_worker.isRunning():
            print("[DEBUG] Stopping current playback...")
            self.playback_worker.stop()
            self.playback_worker.wait()
            print("[DEBUG] Playback stopped")

        # 强制停止当前转换
        if self.tts_worker and self.tts_worker.isRunning():
            print("[DEBUG] Stopping current TTS conversion...")
            self.tts_worker.stop()
            self.tts_worker.wait()
            print("[DEBUG] TTS conversion stopped")

        # 获取总 chunk 数
        from novel_reader.core import get_book
        from novel_reader.utils import load_txt_file, parse_txt
        book = get_book(self.current_book_id)
        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)
        total_chunks = len(chunks)

        # 找到包含 start_chunk 的章节
        from novel_reader.core import get_book_chapters
        book_chapters = get_book_chapters(self.current_book_id)

        print(f"[DEBUG] Found {len(book_chapters)} chapters, total chunks: {total_chunks}")

        # 找到包含 start_chunk 的章节的结束位置
        current_chapter_end = total_chunks  # 默认到文件末尾

        # 遍历章节，找到包含 start_chunk 的章节
        found_chapter_idx = None
        for i, chapter in enumerate(book_chapters):
            chapter_start = chapter['start_chunk']
            # 当前章节的开始位置 <= start_chunk < 下一章的开始位置
            if chapter_start <= start_chunk:
                # 检查是否是包含 start_chunk 的章节
                if i + 1 < len(book_chapters):
                    next_chapter_start_in_loop = book_chapters[i + 1]['start_chunk']
                    if start_chunk < next_chapter_start_in_loop:
                        found_chapter_idx = i
                        current_chapter_end = next_chapter_start_in_loop
                        break
                else:
                    # 最后一章
                    found_chapter_idx = i
                    current_chapter_end = total_chunks
                    break

        if found_chapter_idx is not None:
            print(f"[DEBUG] Found chapter at index {found_chapter_idx}: start={book_chapters[found_chapter_idx]['start_chunk']}, end={current_chapter_end}")

        print(f"[DEBUG] Chapter range: {start_chunk} - {current_chapter_end}")

        # 检查当前章节是否已转换（只检查到章节结束）
        chapter_has_audio = True
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        # 确保范围有效
        if start_chunk >= current_chapter_end:
            print(f"[DEBUG] Invalid range: {start_chunk} >= {current_chapter_end}")
            current_chapter_end = min(start_chunk + 1, total_chunks)

        for i in range(start_chunk, current_chapter_end):
            audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{i:05d}.wav"
            if not Path(audio_path).exists():
                chapter_has_audio = False
                print(f"[DEBUG] Missing audio for chunk {i}")
                break

        print(f"[DEBUG] Chapter has audio: {chapter_has_audio}")

        if chapter_has_audio:
            # 当前章节已转换，直接播放
            chapter_title = book_chapters[found_chapter_idx]['title'] if found_chapter_idx is not None else f"chunk {start_chunk}"
            self.statusBar().showMessage(f"开始播放: {chapter_title}")
            print("[DEBUG] Calling _play_from_chunk")
            self._play_from_chunk(start_chunk)
        else:
            # 当前章节未转换，转换并自动播放
            chapter_title = book_chapters[found_chapter_idx]['title'] if found_chapter_idx is not None else f"chunk {start_chunk}"
            self.statusBar().showMessage(f"转换章节: {chapter_title}")
            print("[DEBUG] Calling _convert_chapter_and_play")
            self._convert_chapter_and_play(self.current_book_id, start_chunk)

    @Slot(int)
    def _on_bookmark_double_clicked(self, chunk: int):
        """书签被双击 - 强制从指定位置播放"""
        self._on_chapter_double_clicked(chunk)

    # ==================== 播放辅助方法 ====================

    def _play_previous_chapter(self):
        """播放上一章"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book, get_book_chapters
        from novel_reader.utils import load_txt_file, parse_txt

        book = get_book(self.current_book_id)
        if not book:
            return

        current_chunk = book['current_chunk']
        chapters = get_book_chapters(self.current_book_id)

        if not chapters:
            QMessageBox.information(self, "提示", "该书没有章节信息")
            return

        # 找到当前chunk所在的章节
        current_chapter_idx = -1
        for i, chapter in enumerate(chapters):
            chapter_start = chapter['start_chunk']
            if i + 1 < len(chapters):
                next_chapter_start = chapters[i + 1]['start_chunk']
                if chapter_start <= current_chunk < next_chapter_start:
                    current_chapter_idx = i
                    break
            else:
                # 最后一章
                if chapter_start <= current_chunk:
                    current_chapter_idx = i
                    break

        # 计算上一章的索引
        prev_chapter_idx = current_chapter_idx - 1

        if prev_chapter_idx < 0:
            QMessageBox.information(self, "提示", "已经是第一章了")
            return

        # 获取上一章的起始chunk
        prev_chapter_start = chapters[prev_chapter_idx]['start_chunk']
        prev_chapter_title = chapters[prev_chapter_idx]['title']

        # 强制停止当前播放
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()

        # 检查上一章是否有音频
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        # 计算上一章的结束位置
        if prev_chapter_idx + 1 < len(chapters):
            chapter_end = chapters[prev_chapter_idx + 1]['start_chunk']
        else:
            text = load_txt_file(book['file_path'])
            chunks, _ = parse_txt(text)
            chapter_end = len(chunks)

        chapter_has_audio = True
        for i in range(prev_chapter_start, chapter_end):
            audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{i:05d}.wav"
            if not Path(audio_path).exists():
                chapter_has_audio = False
                break

        if chapter_has_audio:
            self.statusBar().showMessage(f"开始播放: {prev_chapter_title}")
            self._play_from_chunk(prev_chapter_start)
        else:
            self.statusBar().showMessage(f"转换章节: {prev_chapter_title}")
            self._convert_chapter_and_play(self.current_book_id, prev_chapter_start)

    def _play_next_chapter(self):
        """播放下一章"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book, get_book_chapters
        from novel_reader.utils import load_txt_file, parse_txt

        book = get_book(self.current_book_id)
        if not book:
            return

        current_chunk = book['current_chunk']
        chapters = get_book_chapters(self.current_book_id)

        if not chapters:
            QMessageBox.information(self, "提示", "该书没有章节信息")
            return

        # 找到当前chunk所在的章节
        current_chapter_idx = -1
        for i, chapter in enumerate(chapters):
            chapter_start = chapter['start_chunk']
            if i + 1 < len(chapters):
                next_chapter_start = chapters[i + 1]['start_chunk']
                if chapter_start <= current_chunk < next_chapter_start:
                    current_chapter_idx = i
                    break
            else:
                # 最后一章
                if chapter_start <= current_chunk:
                    current_chapter_idx = i
                    break

        # 计算下一章的索引
        next_chapter_idx = current_chapter_idx + 1

        if next_chapter_idx >= len(chapters):
            QMessageBox.information(self, "提示", "已经是最后一章了")
            return

        # 获取下一章的起始chunk
        next_chapter_start = chapters[next_chapter_idx]['start_chunk']
        next_chapter_title = chapters[next_chapter_idx]['title']

        # 强制停止当前播放
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()

        # 检查下一章是否有音频
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        # 计算下一章的结束位置
        if next_chapter_idx + 1 < len(chapters):
            chapter_end = chapters[next_chapter_idx + 1]['start_chunk']
        else:
            text = load_txt_file(book['file_path'])
            chunks, _ = parse_txt(text)
            chapter_end = len(chunks)

        chapter_has_audio = True
        for i in range(next_chapter_start, chapter_end):
            audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{i:05d}.wav"
            if not Path(audio_path).exists():
                chapter_has_audio = False
                break

        if chapter_has_audio:
            self.statusBar().showMessage(f"开始播放: {next_chapter_title}")
            self._play_from_chunk(next_chapter_start)
        else:
            self.statusBar().showMessage(f"转换章节: {next_chapter_title}")
            self._convert_chapter_and_play(self.current_book_id, next_chapter_start)

    def _play_next_chunk(self):
        """播放下一个分段"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book
        from novel_reader.utils import load_txt_file, parse_txt
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        book = get_book(self.current_book_id)
        if not book:
            return

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

        # 停止当前播放
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()

        # 检查下一个chunk是否有音频
        audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{next_chunk:05d}.wav"

        if Path(audio_path).exists():
            self.statusBar().showMessage(f"跳转到分段 {next_chunk}")
            self._play_from_chunk(next_chunk)
        else:
            # 下一个chunk没有音频，转换后播放
            self.statusBar().showMessage(f"转换分段 {next_chunk}")
            self._convert_chapter_and_play(self.current_book_id, next_chunk)

    def _play_previous_chunk(self):
        """播放上一个分段"""
        if self.current_book_id is None:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path

        book = get_book(self.current_book_id)
        if not book:
            return

        current_chunk = book['current_chunk']

        # 计算上一个chunk
        prev_chunk = current_chunk - 1

        if prev_chunk < 0:
            QMessageBox.information(self, "提示", "已经是第一个分段了")
            return

        # 停止当前播放
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()

        # 检查上一个chunk是否有音频
        audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{prev_chunk:05d}.wav"

        if Path(audio_path).exists():
            self.statusBar().showMessage(f"跳转到分段 {prev_chunk}")
            self._play_from_chunk(prev_chunk)
        else:
            # 上一个chunk没有音频，转换后播放
            self.statusBar().showMessage(f"转换分段 {prev_chunk}")
            self._convert_chapter_and_play(self.current_book_id, prev_chunk)

    def _play_from_chunk(self, start_chunk: int):
        """从指定位置播放"""
        print(f"[DEBUG] _play_from_chunk called: start_chunk={start_chunk}, current_book_id={self.current_book_id}")

        if self.playback_worker and self.playback_worker.isRunning():
            print("[DEBUG] PlaybackWorker already running, returning")
            return

        if self.current_book_id is None:
            print("[DEBUG] No current book selected, returning")
            return

        # 保存最后播放的书籍ID
        from novel_reader.core import set_setting
        set_setting("last_book_id", self.current_book_id)

        # 创建播放工作线程
        self.playback_worker = PlaybackWorker(self.current_book_id, start_chunk)
        self.playback_worker.finished.connect(self._on_playback_finished)
        self.playback_worker.error.connect(self._on_playback_error)
        self.playback_worker.progress_updated.connect(self._on_playback_progress)
        self.playback_worker.chapter_finished.connect(self._on_chapter_playback_finished)
        self.playback_worker.last_chunk_of_chapter_started.connect(self._on_last_chunk_of_chapter_started)
        self.playback_worker.start()

        # 获取书籍信息和当前章节，更新播放显示
        from novel_reader.core import get_book, get_book_chapters
        book = get_book(self.current_book_id)
        if book:
            # 根据start_chunk找到对应的章节
            chapters = get_book_chapters(self.current_book_id)
            chapter_title = ""

            if chapters:
                # 找到包含start_chunk的章节
                for i, chapter in enumerate(chapters):
                    chapter_start = chapter['start_chunk']
                    # 检查这个章节是否包含start_chunk
                    if i + 1 < len(chapters):
                        next_chapter_start = chapters[i + 1]['start_chunk']
                        if chapter_start <= start_chunk < next_chapter_start:
                            chapter_title = chapter['title']
                            break
                    else:
                        # 最后一章
                        if chapter_start <= start_chunk:
                            chapter_title = chapter['title']
                            break

            # 更新播放显示
            self.player_widget.update_current_playback(book['title'], chapter_title)

        # 更新 UI 状态
        self.player_widget.set_playing_state(True)
        self.statusBar().showMessage(f"正在播放 from chunk: {start_chunk}")

    # ==================== TTS 相关槽函数 ====================

    @Slot(int)
    def _convert_book(self, book_id: int):
        """转换书籍"""
        if self.tts_worker and self.tts_worker.isRunning():
            QMessageBox.information(self, "提示", "正在转换中，请稍候")
            return

        # 清空日志
        self.tts_widget.clear_log()
        self.tts_widget.set_converting_state(True)

        # 创建 TTS 工作线程
        self.tts_worker = TTSWorker(book_id)
        self.tts_worker.progress.connect(self._on_tts_progress)
        self.tts_worker.log.connect(self._on_tts_log)
        self.tts_worker.finished.connect(self._on_tts_finished)
        self.tts_worker.error.connect(self._on_tts_error)
        self.tts_worker.start()

        self.statusBar().showMessage(f"正在转换书籍 ID: {book_id}")

    @Slot(int, int)
    def _on_tts_progress(self, current: int, total: int):
        """TTS 进度更新"""
        self.tts_widget.set_progress(current, total)

    @Slot(str)
    def _on_tts_log(self, message: str):
        """TTS 日志"""
        self.tts_widget.add_log(message)

    @Slot()
    def _on_tts_finished(self):
        """TTS 完成"""
        self.tts_widget.set_converting_state(False)
        self.statusBar().showMessage("TTS 转换完成", 3000)

    @Slot(str)
    def _on_tts_error(self, error_msg: str):
        """TTS 错误"""
        self.tts_widget.set_converting_state(False)
        self.tts_widget.add_log(f"错误: {error_msg}")
        QMessageBox.critical(self, "TTS 错误", f"转换失败: {error_msg}")
        self.statusBar().showMessage("TTS 转换失败", 3000)

    def _convert_chapter_and_play(self, book_id: int, start_chunk: int):
        """
        转换当前章节并自动播放

        Args:
            book_id: 书籍 ID
            start_chunk: 起始 chunk ID
        """
        print(f"[DEBUG] _convert_chapter_and_play called: book_id={book_id}, start_chunk={start_chunk}")

        if self.tts_worker and self.tts_worker.isRunning():
            print("[DEBUG] TTS worker already running, returning")
            return

        # 清空日志
        self.tts_widget.clear_log()
        self.tts_widget.set_converting_state(True)

        # 保存起始位置用于播放
        self._pending_play_chunk = start_chunk
        self._conversion_in_progress = True  # 标记转换正在进行

        # 创建 TTS 工作线程（章节模式）
        print(f"[DEBUG] Creating TTSWorker...")
        self.tts_worker = TTSWorker(book_id, start_chunk=start_chunk, chapter_mode=True)
        print(f"[DEBUG] Connecting signals...")
        self.tts_worker.progress.connect(self._on_tts_progress)
        self.tts_worker.log.connect(self._on_tts_log)
        self.tts_worker.first_chunk_ready.connect(self._on_first_chunk_ready)
        self.tts_worker.chapter_finished.connect(self._on_chapter_tts_finished)
        self.tts_worker.finished.connect(self._on_tts_finished)
        self.tts_worker.error.connect(self._on_tts_error)
        print(f"[DEBUG] Starting TTS worker...")
        self.tts_worker.start()
        print(f"[DEBUG] TTS worker started")

        self.statusBar().showMessage(f"正在转换章节 (从 chunk {start_chunk} 开始)...")

    @Slot(int)
    def _on_first_chunk_ready(self, start_chunk: int):
        """
        第一个chunk转换完成，立即开始播放

        Args:
            start_chunk: 起始 chunk ID
        """
        print(f"[DEBUG] First chunk ready, starting playback: {start_chunk}")

        # 检查是否已经在播放
        if self.playback_worker and self.playback_worker.isRunning():
            print("[DEBUG] Already playing, not starting new playback")
            return

        # 验证第一个chunk文件是否存在且有效
        from novel_reader.core.tts import AUDIO_DIR
        from pathlib import Path
        import time

        audio_path = AUDIO_DIR / str(self.current_book_id) / f"chunk_{start_chunk:05d}.wav"

        # 等待文件就绪（最多等待60秒，给TTS转换足够的时间）
        max_wait = 60
        waited = 0
        file_ready = False

        while waited < max_wait:
            if audio_path.exists():
                file_size = audio_path.stat().st_size
                if file_size > 20000:  # 大于20KB认为有效
                    file_ready = True
                    print(f"[DEBUG] File ready: {file_size/1024:.1f} KB")
                    break
                else:
                    print(f"[DEBUG] File too small: {file_size} bytes, waiting...")
            else:
                print(f"[DEBUG] File not exists, waiting...")
            time.sleep(0.5)  # 每0.5秒检查一次
            waited += 0.5

        if not file_ready:
            print(f"[WARNING] First chunk file not ready after {max_wait}s, will retry on next chunk")
            # 清除待播放标记，等待章节完成后再处理
            if hasattr(self, '_pending_play_chunk'):
                delattr(self, '_pending_play_chunk')
            return

        # 如果有待播放的chunk位置，使用它
        if hasattr(self, '_pending_play_chunk'):
            play_chunk = self._pending_play_chunk
            print(f"[DEBUG] Starting playback from pending chunk: {play_chunk}")
            self._play_from_chunk(play_chunk)
        else:
            print(f"[DEBUG] Starting playback from start_chunk: {start_chunk}")
            self._play_from_chunk(start_chunk)

        # 更新状态栏
        self.statusBar().showMessage(f"正在播放，同时继续转换后续章节...")

    @Slot(int, int)
    def _on_chapter_tts_finished(self, chapter_end: int, next_start: int):
        """
        当前章节转换完成（播放已在第一个chunk就绪时开始）

        Args:
            chapter_end: 当前章节结束的 chunk ID
            next_start: 下一章开始的 chunk ID（None 表示最后一章）
        """
        self.tts_widget.add_log(f"✓ 当前章节转换完成！")
        self.statusBar().showMessage(f"章节转换完成")

        # 清理待播放标记
        if hasattr(self, '_pending_play_chunk'):
            delattr(self, '_pending_play_chunk')

        # 提示后台继续转换
        if next_start is not None:
            self.tts_widget.add_log(f"继续在后台转换后续章节 (从 chunk {next_start} 开始)...")
        else:
            self.tts_widget.add_log(f"已到达最后一章")

    # ==================== 帮助相关槽函数 ====================

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

    def _debug_current_chunk(self):
        """调试当前chunk"""
        if not self.current_book_id:
            QMessageBox.warning(self, "警告", "请先选择一本书")
            return

        from novel_reader.core import get_book
        from novel_reader.core.tts import debug_chunk_content

        book = get_book(self.current_book_id)
        current_chunk = book['current_chunk']

        # 调试当前chunk
        debug_info = debug_chunk_content(self.current_book_id, current_chunk)

        if "error" in debug_info:
            QMessageBox.critical(self, "错误", debug_info["error"])
            return

        # 显示调试信息
        msg = f"Chunk {current_chunk} 调试信息:\n\n"
        msg += f"文本长度: {debug_info['text_length']} 字符\n"
        msg += f"文本为空: {'是' if debug_info['text_empty'] else '否'}\n"
        msg += f"音频文件: {debug_info['audio_path']}\n"
        msg += f"音频存在: {'是' if debug_info['audio_exists'] else '否'}\n"

        if debug_info['audio_exists']:
            size_kb = debug_info['audio_size'] / 1024
            msg += f"音频大小: {size_kb:.2f} KB\n"
            if debug_info['audio_size'] < 20000:
                msg += f"⚠ 音频文件过小（<20KB），可能损坏\n"

        msg += f"\n文本预览:\n{debug_info['text_preview']}..."

        QMessageBox.information(self, f"Chunk {current_chunk} 调试", msg)
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    # ==================== 窗口事件 ====================

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有工作线程
        if self.playback_worker and self.playback_worker.isRunning():
            self.playback_worker.stop()
            self.playback_worker.wait()

        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.stop()
            self.tts_worker.wait()

        event.accept()
