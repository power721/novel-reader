#!/usr/bin/env python3
"""
Novel Reader GUI 启动脚本 (新架构版本)

使用新的 PlaybackController 架构运行 GUI
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from novel_reader.gui.pyside_main_v2 import main

if __name__ == "__main__":
    main()
