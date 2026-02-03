#!/usr/bin/env python3
"""
测试电子书转换功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from novel_reader.utils.ebook_converter import (
    get_file_format,
    is_ebook_file,
    convert_ebook_to_txt
)
from novel_reader.models import init_db, get_conn
from novel_reader.core.book import import_book


def test_format_detection():
    """测试文件格式检测"""
    print("=" * 60)
    print("测试文件格式检测")
    print("=" * 60)
    
    test_files = [
        "test.epub",
        "test.mobi",
        "test.azw3",
        "test.azw",
        "test.txt",
        "test.pdf"
    ]
    
    for filename in test_files:
        file_path = Path(filename)
        fmt = get_file_format(file_path)
        is_ebook = is_ebook_file(filename)
        print(f"  {filename:15} → 格式: {fmt:6}  电子书: {is_ebook}")
    
    print()


def test_database_schema():
    """测试数据库字段"""
    print("=" * 60)
    print("测试数据库字段")
    print("=" * 60)
    
    init_db()
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(book)")
    columns = cursor.fetchall()
    
    print("\nbook 表字段:")
    for col in columns:
        print(f"  - {col[1]:20} {col[2]}")
    
    conn.close()
    print()


def test_import_txt():
    """测试导入 TXT 文件"""
    print("=" * 60)
    print("测试导入 TXT 文件")
    print("=" * 60)
    
    test_file = "/tmp/test_book.txt"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""第一章 开始

这是第一章节的内容。这是一个测试文本，用于验证导入功能是否正常工作。

第二章 继续

这是第二章节的内容。继续测试系统的各项功能。

第三章 结束

这是最后一章节的内容。测试完成。
""")
    
    try:
        book_id = import_book(test_file)
        print(f"\n✓ TXT 导入成功，书籍 ID: {book_id}")
        
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, original_filename, file_format
            FROM book WHERE id = ?
        """, (book_id,))
        book = cursor.fetchone()
        
        if book:
            print(f"  书名: {book[0]}")
            print(f"  原始文件名: {book[1]}")
            print(f"  文件格式: {book[2]}")
        
        conn.close()
    except Exception as e:
        print(f"\n✗ TXT 导入失败: {e}")
        import traceback
        traceback.print_exc()


def test_ebook_conversion():
    """测试电子书转换（需要实际文件）"""
    print("=" * 60)
    print("测试电子书转换")
    print("=" * 60)
    
    import os
    
    test_files = [
        "/tmp/test_book.epub",
        "/tmp/test_book.mobi"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"\n  跳过 {test_file}（文件不存在）")
            continue
        
        print(f"\n测试文件: {test_file}")
        
        try:
            txt_path, title = convert_ebook_to_txt(test_file)
            print(f"  ✓ 转换成功")
            print(f"    TXT 文件: {txt_path}")
            print(f"    书名: {title}")
            
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
                print(f"    文本长度: {len(text)} 字符")
                print(f"    文本预览: {text[:100]}...")
        except Exception as e:
            print(f"  ✗ 转换失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "电子书导入功能测试" + " " * 28 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    test_format_detection()
    test_database_schema()
    test_import_txt()
    test_ebook_conversion()
    
    print("\n")
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print()
    print("提示：")
    print("  1. 要测试 EPUB/MOBI 导入，请将测试文件放到 /tmp/test_book.epub 或 /tmp/test_book.mobi")
    print("  2. 使用 pip install EbookLib mobi beautifulsoup4 lxml 安装依赖")
    print("  3. DRM 保护的电子书无法导入")
    print()
