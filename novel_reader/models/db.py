"""
数据库层 - SQLite 数据库初始化和连接管理
"""
import sqlite3
from pathlib import Path

# 数据库文件路径
DB_DIR = Path("data")
DB_PATH = DB_DIR / "library.db"


def get_conn() -> sqlite3.Connection:
    """
    获取数据库连接

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    # 确保数据库目录存在
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=30.0)  # 设置30秒超时
    conn.row_factory = sqlite3.Row  # 返回字典风格的结果

    # 启用 WAL 模式，允许同时读写
    # 这解决了多线程访问数据库时的锁定问题
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')  # 30秒超时

    return conn


def init_db() -> None:
    """
    初始化数据库，创建所有表
    """
    conn = get_conn()
    cursor = conn.cursor()

    # 创建 book 表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS book
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       file_path
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       original_filename
                       TEXT,
                       file_format
                       TEXT,
                       current_chunk
                       INTEGER
                       DEFAULT
                       0,
                       current_chapter
                       INTEGER
                       DEFAULT
                       0,
                       last_played_at
                       TIMESTAMP,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """)

    # 检查并添加新字段（用于升级现有数据库）
    try:
        cursor.execute("SELECT current_chapter FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN current_chapter INTEGER DEFAULT 0")
        print("Added column: book.current_chapter")

    try:
        cursor.execute("SELECT last_played_at FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN last_played_at TIMESTAMP")
        print("Added column: book.last_played_at")

    try:
        cursor.execute("SELECT original_filename FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN original_filename TEXT")
        print("Added column: book.original_filename")

    try:
        cursor.execute("SELECT file_format FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN file_format TEXT")
        print("Added column: book.file_format")

    # 添加阅读位置字段（用于阅读模式）
    try:
        cursor.execute("SELECT reading_position FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN reading_position INTEGER DEFAULT 0")
        print("Added column: book.reading_position")

    # 添加阅读模式章节索引字段（独立于音频模式）
    try:
        cursor.execute("SELECT reading_chapter FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN reading_chapter INTEGER DEFAULT -1")
        print("Added column: book.reading_chapter")

    # 添加 chunk_count 字段
    try:
        cursor.execute("SELECT chunk_count FROM book LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE book ADD COLUMN chunk_count INTEGER DEFAULT 0")
        print("Added column: book.chunk_count")

    # 创建 chapter 表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS chapter
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       book_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       start_chunk
                       INTEGER
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       book_id
                   ) REFERENCES book
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   """)

    # 创建 bookmark 表
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS bookmark
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       book_id
                       INTEGER
                       NOT
                       NULL,
                       chunk
                       INTEGER
                       NOT
                       NULL,
                       note
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       book_id
                   ) REFERENCES book
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   """)

    # 创建索引以提高查询性能
    cursor.execute("""
                   CREATE INDEX IF NOT EXISTS idx_chapter_book_id
                       ON chapter(book_id)
                   """)

    cursor.execute("""
                   CREATE INDEX IF NOT EXISTS idx_bookmark_book_id
                       ON bookmark(book_id)
                   """)

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH.absolute()}")


if __name__ == "__main__":
    # 测试初始化
    init_db()

    # 验证表是否创建成功
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table[0]}")
    conn.close()
