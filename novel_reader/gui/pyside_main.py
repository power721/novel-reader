"""
PySide6 GUI 界面 - 有声书阅读器

主入口文件，启动 PySide6 GUI 应用程序
"""
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from pathlib import Path


def init_database():
    """初始化数据库"""
    from novel_reader.models import init_db
    init_db()


def create_test_data():
    """创建测试数据（可选）"""
    test_file = Path("/tmp/novel_reader_test.txt")

    # 检查是否已存在测试文件
    if test_file.exists():
        return

    print("正在创建测试数据...")

    test_content = """
第一章 旅程开始

这是一个阳光明媚的早晨，主人公踏上了旅程。
前方充满了未知的挑战和机遇。
这里有很多内容，用来测试分段功能。
这些文字会被分成多个 chunk。
每一天都是新的开始，勇敢地面对一切。

第二章 相遇

在旅途中，他遇到了一位神秘的伙伴。
两人决定结伴而行，共同面对困难。
他们一起走过了许多地方。
这段旅程充满了惊喜。
友谊在困难中变得更加坚固。

第三章 危机

突然，一场风暴席卷而来。
他们必须团结一致，才能度过难关。
困难重重，但他们没有放弃。
这是一场考验意志的战斗。
希望的光芒始终在前方闪耀。

第四章 胜利

经过不懈的努力，他们终于战胜了困难。
这段旅程让他们成长了许多。
友谊变得更加深厚。
全文完。
""" * 30

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    # 导入测试书籍
    from novel_reader.core import import_book
    try:
        import_book(str(test_file))
        print("✓ 测试数据创建成功")
    except Exception as e:
        print(f"✗ 测试数据创建失败: {e}")


def run_gui(create_test: bool = False):
    """
    运行 PySide6 GUI 应用程序

    Args:
        create_test: 是否创建测试数据，默认 False
    """
    # 初始化数据库
    init_database()

    # 创建测试数据（可选）
    if create_test:
        create_test_data()

    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.png"))

    # 设置应用程序信息
    app.setApplicationName("Novel Reader")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Novel Reader")

    # Initialize QtAudioPlayer singleton on main thread
    # This prevents threading issues when PlaybackWorker uses it later
    from novel_reader.core.player import _get_player
    _get_player()

    # 创建主窗口
    from .main_window import MainWindow
    window = MainWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


def main():
    """主函数 - 命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Novel Reader - 本地有声书管理器"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="创建测试数据"
    )

    args = parser.parse_args()

    run_gui(create_test=args.test)


if __name__ == "__main__":
    main()
