#!/usr/bin/env python3
"""
GUI 界面启动脚本
"""
import sys


def main():
    """主函数"""
    from novel_reader.models import init_db
    from novel_reader.gui import run_gui

    # 初始化数据库
    init_db()

    # 运行 GUI
    run_gui()


if __name__ == "__main__":
    main()
