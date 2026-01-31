#!/usr/bin/env python3
"""
章节点击功能测试脚本

模拟点击章节并验证转换逻辑
"""
import sys
from pathlib import Path


def test_chapter_logic():
    """测试章节范围计算逻辑"""
    print("=" * 60)
    print("章节点击功能测试")
    print("=" * 60)

    # 初始化数据库
    from novel_reader.models import init_db
    init_db()

    # 获取书籍信息
    from novel_reader.core import get_book, get_book_chapters, list_books
    from novel_reader.utils import load_txt_file, parse_txt
    from novel_reader.core.tts import AUDIO_DIR

    books = list_books()
    if not books:
        print("✗ 没有书籍，请先运行: python -m novel_reader --test")
        return

    # 使用第一本书
    book = books[0]
    book_id = book['id']
    print(f"\n书籍: {book['title']}")
    print(f"ID: {book_id}")
    print(f"当前进度: chunk {book['current_chunk']}")

    # 获取章节列表
    chapters = get_book_chapters(book_id)
    print(f"\n总章节数: {len(chapters)}")

    # 获取总 chunk 数
    text = load_txt_file(book['file_path'])
    chunks, _ = parse_txt(text, chunk_size=800)
    total_chunks = len(chunks)
    print(f"总 chunk 数: {total_chunks}")

    # 模拟点击第 42 章（start_chunk = 41）
    test_chunk = 41
    print(f"\n{'=' * 60}")
    print(f"模拟点击: chunk {test_chunk}")
    print('=' * 60)

    # 找到包含 test_chunk 的章节
    current_chapter_end = total_chunks

    for i, chapter in enumerate(chapters):
        chapter_start = chapter['start_chunk']

        # 确定章节结束位置
        if i + 1 < len(chapters):
            current_chapter_end = chapters[i + 1]['start_chunk']
        else:
            current_chapter_end = total_chunks

        # 如果 test_chunk 在当前章节范围内
        if chapter_start <= test_chunk < current_chapter_end:
            print(f"\n找到章节 {i}:")
            print(f"  章节标题: {chapter['title']}")
            print(f"  起始 chunk: {chapter_start}")
            print(f"  结束 chunk: {current_chapter_end}")
            print(f"  包含 chunk {test_chunk}: ✓")
            break

    print(f"\n章节范围: {test_chunk} - {current_chapter_end}")

    # 检查是否有音频文件
    chapter_has_audio = True
    missing_audio = []

    for i in range(test_chunk, min(current_chapter_end, test_chunk + 5)):  # 只检查前 5 个
        audio_path = AUDIO_DIR / str(book_id) / f"chunk_{i:05d}.wav"
        exists = Path(audio_path).exists()
        if not exists:
            chapter_has_audio = False
            missing_audio.append(i)

        status = "✓" if exists else "✗"
        print(f"  Chunk {i}: {status}")

    if missing_audio:
        print(f"\n缺失的音频文件: {missing_audio[:5]}...")

    print(f"\n章节状态: {'已转换' if chapter_has_audio else '未转换'}")

    # 建议
    if not chapter_has_audio:
        print("\n建议操作:")
        print("  点击该章节 → 自动转换并播放")
        print(f"  转换范围: chunk {test_chunk} - {current_chapter_end}")
    else:
        print("\n建议操作:")
        print("  点击该章节 → 立即播放")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    # 显示书籍列表
    print(f"\n所有书籍:")
    for b in books:
        print(f"  [{b['id']}] {b['title']}")

    # 显示前 5 个和后 5 个章节
    print(f"\n章节列表 (前 5 个):")
    for ch in chapters[:5]:
        print(f"  [{ch['id']:2d}] {ch['title']:40s} → chunk {ch['start_chunk']}")

    if len(chapters) > 5:
        print(f"  ... (共 {len(chapters)} 章)")

    print(f"\n章节列表 (后 5 个):")
    for ch in chapters[-5:]:
        print(f"  [{ch['id']:2d}] {ch['title']:40s} → chunk {ch['start_chunk']}")


def test_auto_selection():
    """测试自动选择逻辑"""
    print("\n" + "=" * 60)
    print("测试自动选择功能")
    print("=" * 60)

    from novel_reader.gui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()

    # 检查是否自动选中了书籍
    if window.current_book_id:
        print(f"✓ 自动选中书籍 ID: {window.current_book_id}")
        book = get_book(window.current_book_id)
        if book:
            print(f"  书名: {book['title']}")
    else:
        print("✗ 没有自动选中书籍")

    window.close()


if __name__ == "__main__":
    test_chapter_logic()
    # test_auto_selection()  # 需要 GUI 环境
