#!/usr/bin/env python3
"""
测试更改书名功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '.')

def test_update_book_title():
    """测试更新书名函数"""
    print("=" * 60)
    print("🧪 测试 update_book_title 函数")
    print("=" * 60)

    from novel_reader.models import init_db
    from novel_reader.core import import_book, get_book, update_book_title

    # 初始化数据库
    init_db()

    # 创建测试文件
    test_file = Path("/tmp/test_rename_book.txt")
    test_content = """
第一章 测试章节

这是测试内容。
"""

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    try:
        # 导入书籍
        print("\n1. 导入测试书籍...")
        book_id = import_book(str(test_file))
        print(f"   ✓ 书籍ID: {book_id}")

        # 获取原始信息
        book = get_book(book_id)
        original_title = book['title']
        print(f"   ✓ 原始书名: {original_title}")

        # 测试更新书名
        print("\n2. 更新书名...")
        new_title = "重命名后的书名"
        success = update_book_title(book_id, new_title)

        if success:
            print(f"   ✓ 更新成功")
        else:
            print(f"   ✗ 更新失败")
            return False

        # 验证更新
        print("\n3. 验证更新结果...")
        book = get_book(book_id)
        if book['title'] == new_title:
            print(f"   ✓ 验证成功: {book['title']}")
        else:
            print(f"   ✗ 验证失败: 期望 '{new_title}', 实际 '{book['title']}'")
            return False

        # 测试空书名
        print("\n4. 测试空书名（应该失败）...")
        success = update_book_title(book_id, "")
        if not success:
            print(f"   ✓ 正确拒绝空书名")
        else:
            print(f"   ✗ 错误：接受了空书名")
            return False

        # 测试只包含空格的书名
        print("\n5. 测试纯空格书名（应该失败）...")
        success = update_book_title(book_id, "   ")
        if not success:
            print(f"   ✓ 正确拒绝纯空格书名")
        else:
            print(f"   ✗ 错误：接受了纯空格书名")
            return False

        # 测试书名trim
        print("\n6. 测试书名trim...")
        success = update_book_title(book_id, "  前后有空格的书名  ")
        book = get_book(book_id)
        if book['title'] == "前后有空格的书名":
            print(f"   ✓ 正确trim: '{book['title']}'")
        else:
            print(f"   ✗ trim失败: '{book['title']}'")
            return False

        print("\n✅ 所有测试通过!")
        return True

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


def test_rename_dialog():
    """测试重命名对话框"""
    print("\n" + "=" * 60)
    print("🧪 测试重命名对话框")
    print("=" * 60)

    from PySide6.QtWidgets import QApplication
    from novel_reader.gui.dialogs import RenameBookDialog

    # 创建应用程序实例
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # 测试对话框创建
    dialog = RenameBookDialog("测试书籍")
    print(f"\n1. 对话框创建成功")
    print(f"   - 标题: {dialog.windowTitle()}")
    print(f"   - 默认值: {dialog.title_input.text()}")

    # 测试获取书名
    new_title = "新的书名"
    dialog.title_input.setText(new_title)
    dialog.new_title = new_title
    result = dialog.get_new_title()

    if result == new_title:
        print(f"\n2. ✓ get_new_title() 正确返回: {result}")
    else:
        print(f"\n2. ✗ get_new_title() 错误: 期望 '{new_title}', 实际 '{result}'")
        return False

    print("\n✅ 对话框测试通过!")
    return True


def test_gui_integration():
    """测试GUI集成"""
    print("\n" + "=" * 60)
    print("🧪 测试GUI集成")
    print("=" * 60)

    from PySide6.QtWidgets import QApplication
    from novel_reader.gui.widgets.book_list_widget import BookListWidget

    # 创建应用程序实例
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # 创建BookListWidget
    widget = BookListWidget()
    print(f"\n1. BookListWidget 创建成功")

    # 测试信号是否存在
    signals = [
        'book_selected',
        'book_double_clicked',
        'books_updated',
        'book_delete_requested',
        'book_rename_requested'  # 新增的信号
    ]

    for signal_name in signals:
        if hasattr(widget, signal_name):
            print(f"   ✓ 信号存在: {signal_name}")
        else:
            print(f"   ✗ 信号缺失: {signal_name}")
            return False

    print("\n✅ GUI集成测试通过!")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 更改书名功能测试套件")
    print("=" * 60)

    all_passed = True

    # 测试核心函数
    if not test_update_book_title():
        all_passed = False

    # 测试对话框
    if all_passed:
        if not test_rename_dialog():
            all_passed = False

    # 测试GUI集成
    if all_passed:
        if not test_gui_integration():
            all_passed = False

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
        print("\n📝 使用方法:")
        print("  1. 在书籍列表中右键点击书籍")
        print("  2. 选择 '✏️ 重命名'")
        print("  3. 输入新的书名")
        print("  4. 点击确定")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
