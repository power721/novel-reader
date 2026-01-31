"""
书籍管理模块 - 导入和查询书籍
"""
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from novel_reader.utils import parse_txt, load_txt_file
from novel_reader.models import get_conn


def import_book(file_path: str) -> int:
    """
    导入书籍（支持重复导入，覆盖章节信息）

    Args:
        file_path: TXT 文件路径

    Returns:
        book_id: 书籍 ID
    """
    # 验证文件存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 读取文件（自动 UTF-8）
    text = load_txt_file(file_path)

    # 解析文本（分段 + 识别章节）
    chunks, chapters = parse_txt(text)

    # 获取文件名作为书名
    title = Path(file_path).stem

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # 检查书籍是否已存在
        cursor.execute("SELECT id FROM book WHERE file_path = ?", (file_path,))
        existing = cursor.fetchone()

        if existing:
            # 书籍已存在，删除旧章节信息
            book_id = existing[0]
            cursor.execute("DELETE FROM chapter WHERE book_id = ?", (book_id,))
            cursor.execute("UPDATE book SET updated_at = ? WHERE id = ?",
                         (datetime.now().isoformat(), book_id))
        else:
            # 创建新书记录
            cursor.execute("""
                INSERT INTO book (title, file_path, current_chunk)
                VALUES (?, ?, 0)
            """, (title, file_path))
            book_id = cursor.lastrowid

        # 插入章节信息
        chapter_records = []
        for chapter_title, start_chunk in chapters:
            cursor.execute("""
                INSERT INTO chapter (book_id, title, start_chunk)
                VALUES (?, ?, ?)
            """, (book_id, chapter_title, start_chunk))
            chapter_records.append((cursor.lastrowid, chapter_title, start_chunk))

        conn.commit()

        print(f"✓ 导入成功: {title}")
        print(f"  书籍 ID: {book_id}")
        print(f"  总段数: {len(chunks)}")
        print(f"  章节数: {len(chapters)}")

        return book_id

    finally:
        conn.close()


def get_book(book_id: int) -> Optional[Dict]:
    """
    获取书籍详情

    Args:
        book_id: 书籍 ID

    Returns:
        书籍信息字典，如果不存在返回 None
    """
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, file_path, current_chunk, current_chapter, last_played_at, created_at, updated_at
        FROM book WHERE id = ?
    """, (book_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "title": row[1],
            "file_path": row[2],
            "current_chunk": row[3],
            "current_chapter": row[4],
            "last_played_at": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
    return None


def get_book_chapters(book_id: int) -> List[Dict]:
    """
    获取书籍的章节列表

    Args:
        book_id: 书籍 ID

    Returns:
        章节列表
    """
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, start_chunk
        FROM chapter
        WHERE book_id = ?
        ORDER BY start_chunk
    """, (book_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "start_chunk": row[2]
        }
        for row in rows
    ]


def list_books() -> List[Dict]:
    """
    列出所有书籍

    Returns:
        书籍列表
    """
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, file_path, current_chunk, current_chapter, last_played_at, created_at, updated_at
        FROM book
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "file_path": row[2],
            "current_chunk": row[3],
            "current_chapter": row[4],
            "last_played_at": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
        for row in rows
    ]


def delete_book(book_id: int, delete_audio: bool = True) -> bool:
    """
    删除书籍

    Args:
        book_id: 书籍 ID
        delete_audio: 是否同时删除音频文件

    Returns:
        是否删除成功
    """
    import shutil
    from novel_reader.core.tts import AUDIO_DIR

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # 获取书籍信息
        cursor.execute("SELECT title FROM book WHERE id = ?", (book_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        book_title = row[0]

        # 删除书签
        cursor.execute("DELETE FROM bookmark WHERE book_id = ?", (book_id,))

        # 删除章节
        cursor.execute("DELETE FROM chapter WHERE book_id = ?", (book_id,))

        # 删除书籍
        cursor.execute("DELETE FROM book WHERE id = ?", (book_id,))

        conn.commit()
        conn.close()

        # 删除音频文件
        if delete_audio:
            book_audio_dir = AUDIO_DIR / str(book_id)
            if book_audio_dir.exists():
                shutil.rmtree(book_audio_dir)
                print(f"✓ 已删除音频文件: {book_audio_dir}")

        print(f"✓ 已删除书籍: {book_title} (ID: {book_id})")
        return True

    except Exception as e:
        conn.close()
        print(f"✗ 删除书籍失败: {e}")
        return False


if __name__ == "__main__":
    # 初始化数据库
    from novel_reader.models import init_db
    init_db()

    # 创建测试文件
    test_file = "/tmp/test_novel.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
第一章 旅程开始

这是一个阳光明媚的早晨，主人公踏上了旅程。
前方充满了未知的挑战和机遇。
这里有很多内容，用来测试分段功能。
这些文字会被分成多个 chunk。

第二章 相遇

在旅途中，他遇到了一位神秘的伙伴。
两人决定结伴而行，共同面对困难。
他们一起走过了许多地方。
这段旅程充满了惊喜。

第三章 危机

突然，一场风暴席卷而来。
他们必须团结一致，才能度过难关。
困难重重，但他们没有放弃。
这是一场考验意志的战斗。

第四章 胜利

经过不懈的努力，他们终于战胜了困难。
这段旅程让他们成长了许多。
友谊变得更加深厚。
全文完。
""" * 50)  # 重复50次以获得更多内容

    print("=" * 60)
    print("测试：导入书籍")
    print("=" * 60)

    # 第一次导入
    print("\n[第一次导入]")
    book_id_1 = import_book(test_file)

    # 第二次导入（同一文件）
    print("\n[第二次导入（同一文件）] 应该覆盖章节")
    book_id_2 = import_book(test_file)

    # 验证是否返回相同的 book_id
    assert book_id_1 == book_id_2, "重复导入应返回相同 book_id"
    print(f"\n✓ 验证通过：两次导入返回相同 ID ({book_id_1})")

    # 查询书籍
    print("\n" + "=" * 60)
    print("查询书籍详情")
    print("=" * 60)
    book = get_book(book_id_1)
    if book:
        print(f"\n书名: {book['title']}")
        print(f"文件: {book['file_path']}")
        print(f"当前进度: chunk {book['current_chunk']}")
        print(f"创建时间: {book['created_at']}")

    # 查询章节
    print("\n" + "=" * 60)
    print("查询章节列表")
    print("=" * 60)
    chapters = get_book_chapters(book_id_1)
    print(f"\n共 {len(chapters)} 章:")
    for ch in chapters:
        print(f"  [{ch['id']:2d}] {ch['title']:20s} → chunk {ch['start_chunk']}")

    # 列出所有书籍
    print("\n" + "=" * 60)
    print("列出所有书籍")
    print("=" * 60)
    books = list_books()
    print(f"\n共 {len(books)} 本书:")
    for b in books:
        print(f"  [{b['id']}] {b['title']}")
