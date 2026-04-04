"""
Tkinter GUI 界面 - 有声书阅读器
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import subprocess
from typing import Optional


class NovelReaderGUI:
    """有声书阅读器 GUI 主窗口"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Novel Reader - 有声书阅读器")
        self.root.geometry("1200x700")

        # 状态变量
        self.current_book_id: Optional[int] = None
        self.is_playing = False
        self.playback_process: Optional[subprocess.Popen] = None

        # 创建界面
        self.create_widgets()

        # 加载数据
        self.load_books()

    def create_widgets(self):
        """创建界面组件"""

        # ==================== 顶部菜单栏 ====================
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入书籍...", command=self.import_book_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

        # ==================== 主容器 ====================
        main_container = ttk.Frame(self.root, padding="5")
        main_container.pack(fill=tk.BOTH, expand=True)

        # ==================== 三栏列表区域 ====================
        lists_frame = ttk.Frame(main_container)
        lists_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：书籍列表
        left_frame = ttk.LabelFrame(lists_frame, text="📚 书籍列表", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.books_tree = ttk.Treeview(left_frame, columns=("ID", "书名", "进度"), show="headings", selectmode="browse")
        self.books_tree.heading("ID", text="ID")
        self.books_tree.heading("书名", text="书名")
        self.books_tree.heading("进度", text="进度")
        self.books_tree.column("ID", width=50)
        self.books_tree.column("书名", width=200)
        self.books_tree.column("进度", width=100)
        self.books_tree.pack(fill=tk.BOTH, expand=True)
        self.books_tree.bind("<<TreeviewSelect>>", self.on_book_selected)
        self.books_tree.bind("<Double-1>", self.on_book_double_click)

        # 书籍滚动条
        books_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.books_tree.yview)
        books_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.books_tree.config(yscrollcommand=books_scrollbar.set)

        # 中间：章节列表
        middle_frame = ttk.LabelFrame(lists_frame, text="📖 章节列表", padding="5")
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.chapters_tree = ttk.Treeview(middle_frame, columns=("ID", "章节标题", "Chunk"), show="headings",
                                          selectmode="browse")
        self.chapters_tree.heading("ID", text="ID")
        self.chapters_tree.heading("章节标题", text="章节标题")
        self.chapters_tree.heading("Chunk", text="Chunk")
        self.chapters_tree.column("ID", width=50)
        self.chapters_tree.column("章节标题", width=200)
        self.chapters_tree.column("Chunk", width=80)
        self.chapters_tree.pack(fill=tk.BOTH, expand=True)
        self.chapters_tree.bind("<Double-1>", self.on_chapter_double_click)

        # 章节滚动条
        chapters_scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.chapters_tree.yview)
        chapters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chapters_tree.config(yscrollcommand=chapters_scrollbar.set)

        # 右侧：书签列表
        right_frame = ttk.LabelFrame(lists_frame, text="🔖 书签列表", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.bookmarks_tree = ttk.Treeview(right_frame, columns=("ID", "位置", "笔记"), show="headings",
                                           selectmode="browse")
        self.bookmarks_tree.heading("ID", text="ID")
        self.bookmarks_tree.heading("位置", text="位置")
        self.bookmarks_tree.heading("笔记", text="笔记")
        self.bookmarks_tree.column("ID", width=50)
        self.bookmarks_tree.column("位置", width=80)
        self.bookmarks_tree.column("笔记", width=200)
        self.bookmarks_tree.pack(fill=tk.BOTH, expand=True)
        self.bookmarks_tree.bind("<Double-1>", self.on_bookmark_double_click)

        # 书签滚动条
        bookmarks_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.bookmarks_tree.yview)
        bookmarks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bookmarks_tree.config(yscrollcommand=bookmarks_scrollbar.set)

        # 书签按钮
        bookmark_btn_frame = ttk.Frame(right_frame)
        bookmark_btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(bookmark_btn_frame, text="添加书签", command=self.add_bookmark).pack(side=tk.LEFT, padx=2)
        ttk.Button(bookmark_btn_frame, text="删除书签", command=self.delete_bookmark).pack(side=tk.LEFT, padx=2)

        # ==================== TTS 转换区域 ====================
        tts_frame = ttk.LabelFrame(main_container, text="🎙️ TTS 转换", padding="5")
        tts_frame.pack(fill=tk.X, pady=5)

        # TTS 控制
        tts_control_frame = ttk.Frame(tts_frame)
        tts_control_frame.pack(fill=tk.X)

        ttk.Button(tts_control_frame, text="转换整本书", command=self.convert_whole_book).pack(side=tk.LEFT, padx=2)
        ttk.Button(tts_control_frame, text="转换选中章节", command=self.convert_selected_chapter).pack(side=tk.LEFT,
                                                                                                       padx=2)

        # TTS 进度
        self.tts_progress = ttk.Progressbar(tts_frame, mode="determinate")
        self.tts_progress.pack(fill=tk.X, pady=2)

        self.tts_status_label = ttk.Label(tts_frame, text="就绪")
        self.tts_status_label.pack(anchor=tk.W)

        # TTS 日志
        self.tts_log = scrolledtext.ScrolledText(tts_frame, height=5, state=tk.DISABLED)
        self.tts_log.pack(fill=tk.BOTH, expand=True)

        # ==================== 播放控制区域 ====================
        player_frame = ttk.LabelFrame(main_container, text="▶️ 播放控制", padding="5")
        player_frame.pack(fill=tk.X, pady=5)

        # 播放按钮
        control_frame = ttk.Frame(player_frame)
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="▶ 播放", command=self.play_book).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏸ 暂停", command=self.pause_playback).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⏹ 停止", command=self.stop_playback).pack(side=tk.LEFT, padx=2)

        # 进度条
        progress_frame = ttk.Frame(player_frame)
        progress_frame.pack(fill=tk.X, pady=2)

        ttk.Label(progress_frame, text="播放进度:").pack(side=tk.LEFT, padx=2)

        self.playback_progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.playback_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.playback_status_label = ttk.Label(progress_frame, text="未播放")
        self.playback_status_label.pack(side=tk.LEFT, padx=2)

        # ==================== 底部状态栏 ====================
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================== 数据加载 ====================

    def load_books(self):
        """加载书籍列表"""
        from novel_reader.core import list_books
        from novel_reader.models import get_conn

        # 清空列表
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)

        books = list_books()

        if not books:
            self.books_tree.insert("", tk.END, values=("-", "暂无书籍", "-"))
            return

        for book in books:
            # 计算总 chunk 数
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM chapter WHERE book_id = ?",
                (book['id'],)
            )
            total_chunks = cursor.fetchone()[0] or 0
            conn.close()

            progress_text = f"{book['current_chunk']}/{total_chunks}"
            self.books_tree.insert("", tk.END, values=(book['id'], book['title'], progress_text))

        self.status_bar.config(text=f"已加载 {len(books)} 本书")

    def load_chapters(self, book_id: int):
        """加载章节列表"""
        from novel_reader.core import get_book_chapters

        # 清空列表
        for item in self.chapters_tree.get_children():
            self.chapters_tree.delete(item)

        chapters = get_book_chapters(book_id)

        if not chapters:
            self.chapters_tree.insert("", tk.END, values=("-", "暂无章节", "-"))
            return

        for chapter in chapters:
            self.chapters_tree.insert("", tk.END, values=(
                chapter['id'],
                chapter['title'],
                chapter['start_chunk']
            ))

    def load_bookmarks(self, book_id: int):
        """加载书签列表"""
        from novel_reader.core import get_bookmarks

        # 清空列表
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)

        bookmarks = get_bookmarks(book_id)

        if not bookmarks:
            self.bookmarks_tree.insert("", tk.END, values=("-", "-", "暂无书签"))
            return

        for bm in bookmarks:
            note = bm['note'] if bm['note'] else ""
            self.bookmarks_tree.insert("", tk.END, values=(
                bm['id'],
                bm['chunk'],
                note[:30] + "..." if len(note) > 30 else note
            ))

    # ==================== 事件处理 ====================

    def on_book_selected(self, event):
        """当选择书籍时"""
        selection = self.books_tree.selection()
        if not selection:
            return

        item = self.books_tree.item(selection[0])
        values = item['values']

        if values[0] == "-":
            return

        self.current_book_id = int(values[0])
        self.load_chapters(self.current_book_id)
        self.load_bookmarks(self.current_book_id)

    def on_book_double_click(self, event):
        """双击书籍播放"""
        self.play_book()

    def on_chapter_double_click(self, event):
        """双击章节播放"""
        selection = self.chapters_tree.selection()
        if not selection:
            return

        item = self.chapters_tree.item(selection[0])
        values = item['values']

        if values[0] == "-" or not values[2]:
            return

        start_chunk = int(values[2])
        self.play_from_chunk(start_chunk)

    def on_bookmark_double_click(self, event):
        """双击书签播放"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            return

        item = self.bookmarks_tree.item(selection[0])
        values = item['values']

        if values[0] == "-" or not values[1]:
            return

        chunk = int(values[1])
        self.play_from_chunk(chunk)

    # ==================== 播放控制 ====================

    def play_book(self):
        """播放当前书籍"""
        if self.current_book_id is None:
            messagebox.showwarning("警告", "请先选择一本书")
            return

        if self.is_playing:
            messagebox.showinfo("提示", "正在播放中，请先停止")
            return

        # 在新线程中播放，避免阻塞 GUI
        threading.Thread(target=self._play_book_thread, daemon=True).start()

    def _play_book_thread(self):
        """播放线程"""
        try:
            from novel_reader.core.player import play_book

            self.is_playing = True
            self.playback_status_label.config(text="正在播放...")

            play_book(self.current_book_id)

        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {e}")
        finally:
            self.is_playing = False
            self.playback_status_label.config(text="未播放")
            self.load_books()  # 刷新进度

    def play_from_chunk(self, chunk: int):
        """从指定 chunk 播放"""
        if self.current_book_id is None:
            messagebox.showwarning("警告", "请先选择一本书")
            return

        if self.is_playing:
            messagebox.showinfo("提示", "正在播放中，请先停止")
            return

        threading.Thread(target=self._play_from_chunk_thread, args=(chunk,), daemon=True).start()

    def _play_from_chunk_thread(self, chunk: int):
        """从指定位置播放线程"""
        try:
            from novel_reader.core.player import play_book

            self.is_playing = True
            self.playback_status_label.config(text=f"正在播放 chunk {chunk}...")

            play_book(self.current_book_id, start_chunk=chunk)

        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {e}")
        finally:
            self.is_playing = False
            self.playback_status_label.config(text="未播放")
            self.load_books()  # 刷新进度

    def pause_playback(self):
        """暂停播放"""
        if self.playback_process:
            self.playback_process.send_signal(subprocess.signal.SIGSTOP)
            self.playback_status_label.config(text="已暂停")

    def stop_playback(self):
        """停止播放"""
        if self.playback_process:
            self.playback_process.terminate()
            self.playback_process = None

        self.is_playing = False
        self.playback_status_label.config(text="未播放")
        self.load_books()  # 刷新进度

    # ==================== 书签管理 ====================

    def add_bookmark(self):
        """添加书签"""
        if self.current_book_id is None:
            messagebox.showwarning("警告", "请先选择一本书")
            return

        from novel_reader.core import get_book, add_bookmark

        book = get_book(self.current_book_id)
        if book is None:
            messagebox.showerror("错误", "书籍不存在")
            return

        current_chunk = book['current_chunk']

        add_bookmark(self.current_book_id, current_chunk, f"Chunk {current_chunk}")

        messagebox.showinfo("成功", f"已添加书签: Chunk {current_chunk}")
        self.load_bookmarks(self.current_book_id)

    def delete_bookmark(self):
        """删除书签"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个书签")
            return

        item = self.bookmarks_tree.item(selection[0])
        values = item['values']

        if values[0] == "-":
            return

        bookmark_id = int(values[0])

        from novel_reader.core import delete_bookmark
        delete_bookmark(bookmark_id)

        messagebox.showinfo("成功", "已删除书签")
        self.load_bookmarks(self.current_book_id)

    # ==================== TTS 转换 ====================

    def convert_whole_book(self):
        """转换整本书"""
        if self.current_book_id is None:
            messagebox.showwarning("警告", "请先选择一本书")
            return

        # 在新线程中转换
        threading.Thread(target=self._convert_book_thread, args=(self.current_book_id,), daemon=True).start()

    def _convert_book_thread(self, book_id: int):
        """TTS 转换线程"""
        try:
            from novel_reader.core import get_book
            from novel_reader.utils import load_txt_file, parse_txt
            from novel_reader.core.tts_engine import convert_chunk, chunk_to_audio_path
            import os

            book = get_book(book_id)
            if book is None:
                return

            self.tts_status_label.config(text="正在转换...")
            self.tts_log_message(f"开始转换: {book['title']}")

            # 读取并解析文本
            text = load_txt_file(book['file_path'])
            chunks, chapters = parse_txt(text)

            total = len(chunks)
            converted = 0

            for i, chunk in enumerate(chunks):
                audio_path = chunk_to_audio_path(book_id, i)

                # 检查是否已存在
                if os.path.exists(audio_path):
                    self.tts_log_message(f"[{i + 1}/{total}] 跳过（已存在）")
                else:
                    self.tts_log_message(f"[{i + 1}/{total}] 正在转换...")
                    try:
                        convert_chunk(chunk, book_id, i)
                        converted += 1
                    except Exception as e:
                        self.tts_log_message(f"[{i + 1}/{total}] 转换失败: {e}")

                # 更新进度
                progress = (i + 1) / total * 100
                self.root.after(0, lambda p=progress: self.tts_progress.config(value=p))

            self.tts_progress.config(value=100)
            self.tts_status_label.config(text=f"转换完成！共转换 {converted}/{total} 个")
            self.tts_log_message(f"转换完成: {book['title']}")

        except Exception as e:
            self.tts_status_label.config(text="转换失败")
            self.tts_log_message(f"错误: {e}")

    def convert_selected_chapter(self):
        """转换选中的章节"""
        messagebox.showinfo("提示", "功能开发中...")

    def tts_log_message(self, message: str):
        """添加 TTS 日志"""
        self.tts_log.config(state=tk.NORMAL)
        self.tts_log.insert(tk.END, message + "\n")
        self.tts_log.see(tk.END)
        self.tts_log.config(state=tk.DISABLED)

    # ==================== 文件操作 ====================

    def import_book_dialog(self):
        """导入书籍对话框"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的 TXT 文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                from novel_reader.core import import_book
                book_id = import_book(file_path)
                messagebox.showinfo("成功", f"导入成功！书籍 ID: {book_id}")
                self.load_books()
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    # ==================== 帮助 ====================

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于 Novel Reader",
            "Novel Reader v0.1.0\n\n"
            "本地有声书管理器\n"
            "支持文本转语音和音频播放\n\n"
            "功能特点:\n"
            "• 完全离线\n"
            "• SQLite 数据库\n"
            "• TTS 转换\n"
            "• 断点续播"
        )


def run_gui():
    """运行 GUI"""
    root = tk.Tk()
    app = NovelReaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # 初始化数据库
    from novel_reader.models import init_db

    init_db()

    # 创建测试数据
    print("正在准备测试数据...")

    from novel_reader.core import import_book

    test_file = "/tmp/gui_test_novel.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
第一章 旅程开始

这是一个阳光明媚的早晨，主人公踏上了旅程。
前方充满了未知的挑战和机遇。

第二章 相遇

在旅途中，他遇到了一位神秘的伙伴。
两人决定结伴而行，共同面对困难。

第三章 危机

突然，一场风暴席卷而来。
他们必须团结一致，才能度过难关。

第四章 胜利

经过不懈的努力，他们终于战胜了困难。
这段旅程让他们成长了许多。
全文完。
""" * 30)

    print("导入测试书籍...")
    import_book(test_file)

    print("\n启动 GUI...")
    run_gui()
