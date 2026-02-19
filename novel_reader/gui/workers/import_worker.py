"""
导入书籍的后台工作线程
避免阻塞 UI 线程
"""
from PySide6.QtCore import QThread, Signal, QObject
from typing import Tuple, Optional, List


class ImportWorker(QThread):
    """导入书籍的后台线程"""

    # 信号定义
    progress_updated = Signal(str)  # 更新进度信息
    import_finished = Signal(int, str)  # 导入成功 (book_id, title)
    import_failed = Signal(str)  # 导入失败 (error_message)
    import_batch_finished = Signal(int, int, list)  # 批量导入完成 (success_count, failed_count, failed_files)

    def __init__(self, file_paths: List[str], parent=None):
        """
        初始化导入工作线程

        Args:
            file_paths: 要导入的文件路径列表
            parent: 父对象
        """
        super().__init__(parent)
        self.file_paths = file_paths

    def run(self):
        """执行导入操作（在后台线程中运行）"""
        success_count = 0
        failed_files = []

        for file_path in self.file_paths:
            try:
                self.progress_updated.emit(f"正在导入: {file_path}")

                # 导入单本书籍
                from novel_reader.core import import_book
                book_id = import_book(file_path)

                # 获取书籍信息
                from novel_reader.core import get_book
                book = get_book(book_id)

                if book:
                    success_count += 1
                    self.import_finished.emit(book_id, book['title'])
                else:
                    failed_files.append((file_path, "无法获取书籍信息"))

            except Exception as e:
                failed_files.append((file_path, str(e)))
                self.import_failed.emit(f"{file_path}: {str(e)}")

        # 发射批量导入完成信号
        self.import_batch_finished.emit(success_count, len(failed_files), failed_files)


class ImportSingleWorker(QThread):
    """导入单本书籍的后台线程"""

    # 信号定义
    progress_updated = Signal(str)  # 更新进度信息
    import_finished = Signal(int, str)  # 导入成功 (book_id, title)
    import_failed = Signal(str)  # 导入失败 (error_message)

    def __init__(self, file_path: str, parent=None):
        """
        初始化导入工作线程

        Args:
            file_path: 要导入的文件路径
            parent: 父对象
        """
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        """执行导入操作（在后台线程中运行）"""
        try:
            self.progress_updated.emit("正在导入书籍...")

            # 检查文件格式
            from pathlib import Path
            from novel_reader.utils.ebook_converter import is_ebook_file

            file_suffix = Path(self.file_path).suffix.lower()

            # 验证文件格式
            if file_suffix != '.txt' and not is_ebook_file(self.file_path):
                self.import_failed.emit(f"不支持的文件格式: {file_suffix}")
                return

            # 导入书籍
            from novel_reader.core import import_book
            book_id = import_book(self.file_path)

            # 获取书籍信息
            from novel_reader.core import get_book
            book = get_book(book_id)

            if book:
                self.import_finished.emit(book_id, book['title'])
            else:
                self.import_failed.emit("无法获取书籍信息")

        except FileNotFoundError as e:
            self.import_failed.emit(f"文件不存在: {str(e)}")
        except Exception as e:
            self.import_failed.emit(f"导入失败: {str(e)}")
