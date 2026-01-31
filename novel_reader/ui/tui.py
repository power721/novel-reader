"""
Textual TUI 界面 - 有声书阅读器
"""
import subprocess
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, DataTable, Static, Button, Label
)
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual import on


class NovelReaderApp(App):
    """有声书阅读器主界面"""

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("b", "add_bookmark", "添加书签", show=True),
        Binding("left,h", "focus_left", "左移", show=False),
        Binding("right,l", "focus_right", "右移", show=False),
        Binding("up,k", "focus_up", "上移", show=False),
        Binding("down,j", "focus_down", "下移", show=False),
        Binding("enter", "play_selected", "播放", show=False),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    DataTable {
        height: 1fr;
    }

    .panel {
        border: thick $primary;
        padding: 1;
    }

    .panel-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #status-bar {
        height: 3;
        dock: top;
        background: $panel;
        text-align: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_book_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        """构建界面"""
        yield Header()
        yield Static(" [b:添加书签 | Enter:播放选中项 | 方向键导航 | q:退出] ", id="status-bar")

        with Horizontal(id="main"):
            # 左侧：书籍列表
            with Vertical(classes="panel"):
                yield Static("📚 书籍列表", classes="panel-title")
                yield DataTable(id="books-table")

            # 中间：章节列表
            with Vertical(classes="panel"):
                yield Static("📖 章节列表", classes="panel-title")
                yield DataTable(id="chapters-table")

            # 右侧：书签列表
            with Vertical(classes="panel"):
                yield Static("🔖 书签列表", classes="panel-title")
                yield DataTable(id="bookmarks-table")

        yield Footer()

    def on_mount(self) -> None:
        """界面加载完成后初始化"""
        # 设置表格列
        books_table = self.query_one("#books-table", DataTable)
        books_table.add_column("ID", width=6)
        books_table.add_column("书名", width=20)
        books_table.add_column("进度", width=10)

        chapters_table = self.query_one("#chapters-table", DataTable)
        chapters_table.add_column("ID", width=6)
        chapters_table.add_column("章节标题", width=30)
        chapters_table.add_column("Chunk", width=8)

        bookmarks_table = self.query_one("#bookmarks-table", DataTable)
        bookmarks_table.add_column("ID", width=6)
        bookmarks_table.add_column("位置", width=8)
        bookmarks_table.add_column("笔记", width=20)

        # 设置表格行选择
        for table_id in ["#books-table", "#chapters-table", "#bookmarks-table"]:
            table = self.query_one(table_id, DataTable)
            table.cursor_type = "row"

        # 加载数据
        self.load_books()

    def load_books(self):
        """加载书籍列表"""
        from novel_reader.core import list_books
        from novel_reader.models import get_conn

        books_table = self.query_one("#books-table", DataTable)
        books_table.clear()

        books = list_books()

        if not books:
            books_table.add_row("-", "暂无书籍", "-")
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
            books_table.add_row(
                str(book['id']),
                book['title'],
                progress_text
            )

    def on_book_selected(self, event) -> None:
        """当选择书籍时"""
        books_table = self.query_one("#books-table", DataTable)
        if books_table.row_count == 0:
            return

        row_key = books_table.cursor_row
        cell = books_table.get_cell(row_key, "ID")

        if cell == "-":
            return

        self.current_book_id = int(cell)
        self.load_chapters(self.current_book_id)
        self.load_bookmarks(self.current_book_id)

    def load_chapters(self, book_id: int):
        """加载章节列表"""
        from novel_reader.core import get_book_chapters

        chapters_table = self.query_one("#chapters-table", DataTable)
        chapters_table.clear()

        chapters = get_book_chapters(book_id)

        if not chapters:
            chapters_table.add_row("-", "暂无章节", "-")
            return

        for chapter in chapters:
            chapters_table.add_row(
                str(chapter['id']),
                chapter['title'],
                str(chapter['start_chunk'])
            )

    def load_bookmarks(self, book_id: int):
        """加载书签列表"""
        from novel_reader.models import get_conn

        bookmarks_table = self.query_one("#bookmarks-table", DataTable)
        bookmarks_table.clear()

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, chunk, note
            FROM bookmark
            WHERE book_id = ?
            ORDER BY chunk
        """, (book_id,))

        bookmarks = cursor.fetchall()
        conn.close()

        if not bookmarks:
            bookmarks_table.add_row("-", "-", "暂无书签")
            return

        for bm in bookmarks:
            note = bm[2] if bm[2] else ""
            bookmarks_table.add_row(
                str(bm[0]),
                str(bm[1]),
                note[:20] + "..." if len(note) > 20 else note
            )

    def _get_focused_table(self) -> Optional[DataTable]:
        """获取当前聚焦的表格"""
        focused = self.focused
        if isinstance(focused, DataTable):
            return focused
        return None

    def action_play_selected(self) -> None:
        """播放当前选中的项目（书籍/章节/书签）"""
        table = self._get_focused_table()

        if table is None:
            self.notify("请先选择一个项目", severity="warning")
            return

        table_id = table.id

        if table_id == "books-table":
            # 播放书籍
            self.action_play_book()

        elif table_id == "chapters-table":
            # 播放章节
            self.action_play_chapter()

        elif table_id == "bookmarks-table":
            # 播放书签
            self.action_play_bookmark()

    def action_play_book(self) -> None:
        """播放当前选中的书籍"""
        if self.current_book_id is None:
            self.notify("请先选择一本书", severity="warning")
            return

        book_id = self.current_book_id
        self.exit()

        print(f"\n开始播放书籍 ID: {book_id}")
        print("按 Ctrl+C 停止播放\n")

        try:
            from novel_reader.core.player import play_book
            play_book(book_id)
        except Exception as e:
            print(f"播放失败: {e}")

    def action_play_chapter(self) -> None:
        """从当前选中的章节开始播放"""
        if self.current_book_id is None:
            self.notify("请先选择一本书", severity="warning")
            return

        chapters_table = self.query_one("#chapters-table", DataTable)

        if chapters_table.row_count == 0:
            self.notify("暂无章节", severity="warning")
            return

        row_key = chapters_table.cursor_row
        cell = chapters_table.get_cell(row_key, "Chunk")

        if cell == "-" or not cell:
            self.notify("请选择有效的章节", severity="warning")
            return

        start_chunk = int(cell)
        book_id = self.current_book_id

        self.exit()

        print(f"\n从 chunk {start_chunk} 开始播放")
        print("按 Ctrl+C 停止播放\n")

        try:
            from novel_reader.core.player import play_book
            play_book(book_id, start_chunk=start_chunk)
        except Exception as e:
            print(f"播放失败: {e}")

    def action_play_bookmark(self) -> None:
        """从当前选中的书签位置开始播放"""
        if self.current_book_id is None:
            self.notify("请先选择一本书", severity="warning")
            return

        bookmarks_table = self.query_one("#bookmarks-table", DataTable)

        if bookmarks_table.row_count == 0:
            self.notify("暂无书签", severity="warning")
            return

        row_key = bookmarks_table.cursor_row
        cell = bookmarks_table.get_cell(row_key, "位置")

        if cell == "-" or not cell:
            self.notify("请选择有效的书签", severity="warning")
            return

        chunk = int(cell)
        book_id = self.current_book_id

        self.exit()

        print(f"\n从书签位置 chunk {chunk} 开始播放")
        print("按 Ctrl+C 停止播放\n")

        try:
            from novel_reader.core.player import play_book
            play_book(book_id, start_chunk=chunk)
        except Exception as e:
            print(f"播放失败: {e}")

    def action_add_bookmark(self) -> None:
        """添加书签到当前播放位置"""
        if self.current_book_id is None:
            self.notify("请先选择一本书", severity="warning")
            return

        from novel_reader.core import get_book, add_bookmark

        # 获取当前书籍的进度
        book = get_book(self.current_book_id)
        if book is None:
            self.notify("书籍不存在", severity="error")
            return

        current_chunk = book['current_chunk']

        # 添加书签
        bookmark_id = add_bookmark(
            self.current_book_id,
            current_chunk,
            f"Chunk {current_chunk}"
        )

        self.notify(f"✓ 已添加书签: Chunk {current_chunk}", severity="success")

        # 刷新书签列表
        self.load_bookmarks(self.current_book_id)


def run_tui():
    """运行 TUI 界面"""
    app = NovelReaderApp()
    app.run()


if __name__ == "__main__":
    # 初始化数据库
    from novel_reader.models import init_db
    init_db()

    # 创建一些测试数据
    print("正在准备测试数据...")

    from novel_reader.core import import_book
    test_file = "/tmp/tui_test_novel.txt"
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

    print("\n" + "=" * 60)
    print("启动 TUI 界面...")
    print("=" * 60)
    print("\n操作说明:")
    print("  方向键 / hjkl  - 导航")
    print("  Enter          - 播放选中项（书籍/章节/书签）")
    print("  b              - 添加书签到当前进度")
    print("  q              - 退出")
    print("\n")

    # 运行 TUI
    run_tui()
