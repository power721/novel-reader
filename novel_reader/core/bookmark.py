"""
书签管理模块
"""
from novel_reader.models import get_conn
from typing import List, Dict, Optional


def add_bookmark(book_id: int, chunk: int, note: str = "") -> int:
    """
    添加书签

    Args:
        book_id: 书籍 ID
        chunk: chunk ID
        note: 笔记（可选）

    Returns:
        书签 ID
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO bookmark (book_id, chunk, note)
            VALUES (?, ?, ?)
        """, (book_id, chunk, note))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def get_bookmarks(book_id: int) -> List[Dict]:
    """
    获取书籍的所有书签

    Args:
        book_id: 书籍 ID

    Returns:
        书签列表
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, book_id, chunk, note, created_at
            FROM bookmark
            WHERE book_id = ?
            ORDER BY chunk
        """, (book_id,))

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "book_id": row[1],
                "chunk": row[2],
                "note": row[3],
                "created_at": row[4]
            }
            for row in rows
        ]

    finally:
        conn.close()


def delete_bookmark(bookmark_id: int) -> bool:
    """
    删除书签

    Args:
        bookmark_id: 书签 ID

    Returns:
        是否成功
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM bookmark WHERE id = ?", (bookmark_id,))
        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


def update_bookmark(bookmark_id: int, note: str) -> bool:
    """
    更新书签笔记

    Args:
        bookmark_id: 书签 ID
        note: 新笔记

    Returns:
        是否成功
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE bookmark
            SET note = ?
            WHERE id = ?
        """, (note, bookmark_id))

        conn.commit()
        return cursor.rowcount > 0

    finally:
        conn.close()


if __name__ == "__main__":
    from novel_reader.models import init_db

    # 测试
    init_db()

    print("测试书签功能...")

    # 添加书签
    bookmark_id = add_bookmark(1, 10, "重要章节")
    print(f"✓ 添加书签: ID={bookmark_id}")

    # 获取书签
    bookmarks = get_bookmarks(1)
    print(f"✓ 查询书签: 共 {len(bookmarks)} 个")
    for bm in bookmarks:
        print(f"  [{bm['id']}] chunk {bm['chunk']}: {bm['note']}")

    # 更新书签
    update_bookmark(bookmark_id, "更新后的笔记")
    print(f"✓ 更新书签: ID={bookmark_id}")

    # 删除书签
    delete_bookmark(bookmark_id)
    print(f"✓ 删除书签: ID={bookmark_id}")
