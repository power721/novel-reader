"""
Novel Reader - 本地有声书管理器

使用方式:
    python -m novel_reader              # 运行 GUI
    python -m novel_reader --test       # 运行 GUI 并创建测试数据
"""
import sys


def main():
    """主函数 - 运行 PySide6 GUI"""
    from novel_reader.gui.pyside_main import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
