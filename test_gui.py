#!/usr/bin/env python3
"""
GUI 功能验证脚本

验证所有组件是否可以正确导入和初始化
"""
import sys


def test_imports():
    """测试所有模块导入"""
    print("Testing imports...")

    # 测试核心模块
    from novel_reader.core import (
        import_book, get_book, list_books, get_book_chapters,
        add_bookmark, get_bookmarks, delete_bookmark
    )
    print("  ✓ Core modules imported")

    # 测试 GUI 组件
    from novel_reader.gui.widgets import (
        BookListWidget, ChapterListWidget,
        BookmarkListWidget, PlayerWidget, TTSWidget
    )
    print("  ✓ GUI widgets imported")

    # 测试工作线程
    from novel_reader.gui.workers import PlaybackWorker, TTSWorker
    print("  ✓ Workers imported")

    # 测试对话框
    from novel_reader.gui.dialogs import AboutDialog
    print("  ✓ Dialogs imported")

    # 测试主窗口
    from novel_reader.gui.main_window import MainWindow
    print("  ✓ Main window imported")


def test_widget_instantiation():
    """测试组件实例化"""
    print("\nTesting widget instantiation...")

    from PySide6.QtWidgets import QApplication
    from novel_reader.gui.widgets import (
        BookListWidget, ChapterListWidget,
        BookmarkListWidget, PlayerWidget, TTSWidget
    )

    # 创建应用实例
    app = QApplication.instance() or QApplication(sys.argv)

    # 测试各组件
    BookListWidget()
    print("  ✓ BookListWidget created")

    ChapterListWidget()
    print("  ✓ ChapterListWidget created")

    BookmarkListWidget()
    print("  ✓ BookmarkListWidget created")

    PlayerWidget()
    print("  ✓ PlayerWidget created")

    TTSWidget()
    print("  ✓ TTSWidget created")


def test_main_window():
    """测试主窗口"""
    print("\nTesting main window...")

    from PySide6.QtWidgets import QApplication
    from novel_reader.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    print("  ✓ MainWindow created")

    # 验证关键属性
    assert hasattr(window, 'book_list_widget')
    assert hasattr(window, 'chapter_list_widget')
    assert hasattr(window, 'bookmark_list_widget')
    assert hasattr(window, 'player_widget')
    assert hasattr(window, 'tts_widget')
    print("  ✓ All widgets present")

    window.close()


def test_database():
    """测试数据库"""
    print("\nTesting database...")

    from novel_reader.models import init_db, get_conn

    init_db()
    print("  ✓ Database initialized")

    conn = get_conn()
    cursor = conn.cursor()

    # 验证表存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    assert 'book' in tables
    assert 'chapter' in tables
    assert 'bookmark' in tables
    print("  ✓ All tables exist")

    conn.close()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("GUI Functionality Test")
    print("=" * 60)

    try:
        test_imports()
        test_widget_instantiation()
        test_main_window()
        test_database()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
