"""
主题管理模块 - 管理应用程序的亮色/暗色主题
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


class Theme:
    """主题颜色定义"""

    def __init__(self, name: str):
        self.name = name

    def get_stylesheet(self) -> str:
        """获取主题样式表"""
        raise NotImplementedError


class LightTheme(Theme):
    """亮色主题"""

    def __init__(self):
        super().__init__("light")
        # 调色板颜色
        self.window_bg = QColor(255, 255, 255)
        self.window_text = QColor(0, 0, 0)
        self.base_bg = QColor(255, 255, 255)
        self.alternate_base = QColor(245, 245, 245)
        self.text = QColor(0, 0, 0)
        self.button_bg = QColor(240, 240, 240)
        self.button_text = QColor(0, 0, 0)
        self.highlight = QColor(76, 110, 245)
        self.highlighted_text = QColor(255, 255, 255)

    def get_palette(self) -> QPalette:
        """获取亮色主题调色板"""
        palette = QPalette()
        palette.setColor(QPalette.Window, self.window_bg)
        palette.setColor(QPalette.WindowText, self.window_text)
        palette.setColor(QPalette.Base, self.base_bg)
        palette.setColor(QPalette.AlternateBase, self.alternate_base)
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, self.text)
        palette.setColor(QPalette.Button, self.button_bg)
        palette.setColor(QPalette.ButtonText, self.button_text)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, self.highlight)
        palette.setColor(QPalette.HighlightedText, self.highlighted_text)
        return palette

    def get_stylesheet(self) -> str:
        """获取亮色主题样式表"""
        return """
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }

        QMainWindow {
            background-color: #f5f5f5;
        }

        QSplitter::handle {
            background-color: #d0d0d0;
        }

        QSplitter::handle:hover {
            background-color: #a0a0a0;
        }

        QGroupBox {
            border: 1px solid #d0d0d0;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #b0b0b0;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #e0e0e0;
        }

        QPushButton:pressed {
            background-color: #d0d0d0;
        }

        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #a0a0a0;
        }

        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 3px;
            padding: 3px;
        }

        QLineEdit:focus {
            border: 1px solid #4c6ef5;
        }

        QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 3px;
        }

        QListWidget, QTreeWidget, QTableWidget {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            selection-background-color: #4c6ef5;
            selection-color: #ffffff;
            alternate-background-color: #f5f5f5;
        }

        QScrollBar:vertical {
            background-color: #f5f5f5;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background-color: #b0b0b0;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #909090;
        }

        QScrollBar:horizontal {
            background-color: #f5f5f5;
            height: 12px;
        }

        QScrollBar::handle:horizontal {
            background-color: #b0b0b0;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #909090;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            width: 16px;
            background: #4c6ef5;
            border-radius: 8px;
            margin: -5px 0;
        }

        QSlider::handle:horizontal:hover {
            background: #3b5bdb;
        }

        QProgressBar {
            border: 1px solid #d0d0d0;
            border-radius: 5px;
            background-color: #f5f5f5;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #4c6ef5;
            border-radius: 4px;
        }

        QMenuBar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #d0d0d0;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 5px 10px;
        }

        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }

        QMenu {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
        }

        QMenu::item {
            padding: 5px 30px 5px 20px;
        }

        QMenu::item:selected {
            background-color: #4c6ef5;
            color: #ffffff;
        }

        QStatusBar {
            background-color: #f5f5f5;
            border-top: 1px solid #d0d0d0;
        }

        QTabWidget::pane {
            border: 1px solid #d0d0d0;
            background-color: #ffffff;
        }

        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #d0d0d0;
            border-bottom: none;
            padding: 5px 15px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }

        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        """


class DarkTheme(Theme):
    """暗色主题"""

    def __init__(self):
        super().__init__("dark")
        # 调色板颜色
        self.window_bg = QColor(53, 53, 53)
        self.window_text = QColor(255, 255, 255)
        self.base_bg = QColor(25, 25, 25)
        self.alternate_base = QColor(53, 53, 53)
        self.text = QColor(255, 255, 255)
        self.button_bg = QColor(53, 53, 53)
        self.button_text = QColor(255, 255, 255)
        self.highlight = QColor(42, 130, 218)
        self.highlighted_text = QColor(0, 0, 0)

    def get_palette(self) -> QPalette:
        """获取暗色主题调色板"""
        palette = QPalette()
        palette.setColor(QPalette.Window, self.window_bg)
        palette.setColor(QPalette.WindowText, self.window_text)
        palette.setColor(QPalette.Base, self.base_bg)
        palette.setColor(QPalette.AlternateBase, self.alternate_base)
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, self.text)
        palette.setColor(QPalette.Button, self.button_bg)
        palette.setColor(QPalette.ButtonText, self.button_text)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, self.highlight)
        palette.setColor(QPalette.HighlightedText, self.highlighted_text)
        return palette

    def get_stylesheet(self) -> str:
        """获取暗色主题样式表"""
        return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QMainWindow {
            background-color: #1e1e1e;
        }

        QSplitter::handle {
            background-color: #3a3a3a;
        }

        QSplitter::handle:hover {
            background-color: #505050;
        }

        QGroupBox {
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QPushButton {
            background-color: #353535;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 80px;
        }

        QPushButton:hover {
            background-color: #454545;
        }

        QPushButton:pressed {
            background-color: #555;
        }

        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #666;
        }

        QLineEdit {
            background-color: #1e1e1e;
            border: 1px solid #3a3a3a;
            border-radius: 3px;
            padding: 3px;
            color: #ffffff;
        }

        QLineEdit:focus {
            border: 1px solid #4c8bf5;
        }

        QTextEdit, QPlainTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #3a3a3a;
            border-radius: 3px;
            color: #ffffff;
        }

        QListWidget, QTreeWidget, QTableWidget {
            background-color: #1e1e1e;
            border: 1px solid #3a3a3a;
            selection-background-color: #2a82da;
            selection-color: #ffffff;
            alternate-background-color: #2b2b2b;
            color: #ffffff;
        }

        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background-color: #555;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #666;
        }

        QScrollBar:horizontal {
            background-color: #2b2b2b;
            height: 12px;
        }

        QScrollBar::handle:horizontal {
            background-color: #555;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #666;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background: #3a3a3a;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            width: 16px;
            background: #4c8bf5;
            border-radius: 8px;
            margin: -5px 0;
        }

        QSlider::handle:horizontal:hover {
            background: #5a9bff;
        }

        QProgressBar {
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            background-color: #2b2b2b;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #2a82da;
            border-radius: 4px;
        }

        QMenuBar {
            background-color: #2b2b2b;
            border-bottom: 1px solid #3a3a3a;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 5px 10px;
        }

        QMenuBar::item:selected {
            background-color: #3a3a3a;
        }

        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #3a3a3a;
        }

        QMenu::item {
            padding: 5px 30px 5px 20px;
        }

        QMenu::item:selected {
            background-color: #2a82da;
            color: #ffffff;
        }

        QStatusBar {
            background-color: #2b2b2b;
            border-top: 1px solid #3a3a3a;
        }

        QTabWidget::pane {
            border: 1px solid #3a3a3a;
            background-color: #1e1e1e;
        }

        QTabBar::tab {
            background-color: #353535;
            border: 1px solid #3a3a3a;
            border-bottom: none;
            padding: 5px 15px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background-color: #1e1e1e;
            border-bottom: 1px solid #1e1e1e;
        }

        QTabBar::tab:hover {
            background-color: #454545;
        }
        """


class ThemeManager:
    """主题管理器"""

    # 可用主题
    THEMES = {
        "light": LightTheme(),
        "dark": DarkTheme(),
    }

    @classmethod
    def get_available_themes(cls) -> list[str]:
        """获取可用主题列表"""
        return list(cls.THEMES.keys())

    @classmethod
    def apply_theme(cls, theme_name: str, app: QApplication = None) -> None:
        """
        应用主题

        Args:
            theme_name: 主题名称 ("light" 或 "dark")
            app: QApplication 实例，如果为 None 则获取当前实例
        """
        if app is None:
            app = QApplication.instance()

        if app is None:
            return

        if theme_name not in cls.THEMES:
            print(f"警告: 未知的主题 '{theme_name}'，使用默认主题 'light'")
            theme_name = "light"

        theme = cls.THEMES[theme_name]

        # 应用 Fusion 样式（提供更好的跨平台一致性）
        app.setStyle("Fusion")

        # 应用调色板
        app.setPalette(theme.get_palette())

        # 应用样式表
        app.setStyleSheet(theme.get_stylesheet())

        print(f"✓ 已应用主题: {theme.name}")

    @classmethod
    def get_theme(cls, theme_name: str) -> Theme:
        """获取主题对象"""
        if theme_name not in cls.THEMES:
            theme_name = "light"
        return cls.THEMES[theme_name]


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    print("=" * 60)
    print("主题管理测试")
    print("=" * 60)

    # 测试可用主题
    print("\n[1] 可用主题:")
    for theme_name in ThemeManager.get_available_themes():
        print(f"  - {theme_name}")

    # 测试应用亮色主题
    print("\n[2] 应用亮色主题:")
    ThemeManager.apply_theme("light")

    # 测试应用暗色主题
    print("\n[3] 应用暗色主题:")
    ThemeManager.apply_theme("dark")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
