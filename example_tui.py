#!/usr/bin/env python3
"""
TUI 界面测试和演示
"""
import sys


def test_tui():
    """测试 TUI 界面"""
    from novel_reader.models import init_db
    from novel_reader.core import import_book
    from novel_reader.ui.tui import run_tui

    # 初始化数据库
    init_db()

    # 创建测试书籍
    print("正在准备测试数据...")

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
    print("  Enter          - 播放选中的书籍")
    print("  q              - 退出")
    print("\n")

    # 运行 TUI
    run_tui()


if __name__ == "__main__":
    test_tui()
