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

    # 确保时间戳使用 UTC 时间
    conn.execute('PRAGMA timezone=UTC')

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
                       reading_position
                       INTEGER
                       DEFAULT
                       0,
                       reading_chapter
                       INTEGER
                       DEFAULT
                       -1,
                       chunk_count
                       INTEGER
                       DEFAULT
                       0,
                       reading_time
                       INTEGER
                       DEFAULT
                       0,
                       last_played_at
                       TIMESTAMP,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       (datetime('now')),
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       (datetime('now'))
                   )
                   """)

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
                       word_count
                       INTEGER
                       DEFAULT
                       0,
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
                       chapter_id
                       INTEGER,
                       chapter_title
                       TEXT,
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
