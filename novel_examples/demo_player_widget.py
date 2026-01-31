#!/usr/bin/env python3
"""
演示PlayerWidget的播放信息显示功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '.')

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from novel_reader.gui.widgets.player_widget import PlayerWidget


class DemoWindow(QWidget):
    """演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlayerWidget 播放信息显示演示")
        self.resize(600, 300)

        layout = QVBoxLayout(self)

        # 添加PlayerWidget
        self.player_widget = PlayerWidget()
        layout.addWidget(self.player_widget)

        # 添加测试按钮
        test_layout = QVBoxLayout()

        btn1 = QPushButton("测试1: 设置书籍")
        btn1.clicked.connect(lambda: self._test_set_book())
        test_layout.addWidget(btn1)

        btn2 = QPushButton("测试2: 更新播放信息 (书名 + 章节)")
        btn2.clicked.connect(lambda: self._test_update_info())
        test_layout.addWidget(btn2)

        btn3 = QPushButton("测试3: 播放状态")
        btn3.clicked.connect(lambda: self._test_playing_state())
        test_layout.addWidget(btn3)

        btn4 = QPushButton("测试4: 暂停状态")
        btn4.clicked.connect(lambda: self._test_paused_state())
        test_layout.addWidget(btn4)

        btn5 = QPushButton("测试5: 重置")
        btn5.clicked.connect(lambda: self._test_reset())
        test_layout.addWidget(btn5)

        layout.addLayout(test_layout)

        # 初始状态
        self.player_widget.set_book(1, "三体")

    def _test_set_book(self):
        """测试设置书籍"""
        print("[测试] 设置书籍")
        self.player_widget.set_book(1, "三体")

    def _test_update_info(self):
        """测试更新播放信息"""
        print("[测试] 更新播放信息")
        self.player_widget.update_current_playback(
            "三体",
            "第一章 科学边界"
        )

    def _test_playing_state(self):
        """测试播放状态"""
        print("[测试] 播放状态")
        self.player_widget.set_playing_state(True)

    def _test_paused_state(self):
        """测试暂停状态"""
        print("[测试] 暂停状态")
        self.player_widget.set_paused_state(True)

    def _test_reset(self):
        """测试重置"""
        print("[测试] 重置")
        self.player_widget.reset()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    window = DemoWindow()
    window.show()

    print("=" * 60)
    print("PlayerWidget 播放信息显示演示")
    print("=" * 60)
    print("\n功能说明:")
    print("  - 播放控制组件顶部显示当前播放的书名和章节")
    print("  - 显示信息会随播放状态动态更新")
    print("  - 支持以下格式:")
    print("    * 未选择书籍 (灰色斜体)")
    print("    * 书籍 ID: X (灰色)")
    print("    * 书名 - 章节 (蓝色加粗)")
    print("\n请点击按钮测试不同状态\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
