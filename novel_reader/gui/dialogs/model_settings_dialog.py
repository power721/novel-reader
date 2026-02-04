"""
TTS 模型设置对话框

用于选择和管理 TTS 模型
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QProgressBar, QGroupBox,
    QMessageBox, QTreeWidgetItem, QTreeWidget, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
from typing import Optional


class ModelDownloadThread(QThread):
    """模型下载线程"""
    progress = Signal(str, int, int)  # (filename, current, total)
    finished = Signal(bool, str)  # (success, message)

    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id

    def run(self):
        """执行下载"""
        from novel_reader.core.model_downloader import download_model

        def progress_callback(filename: str, current: int, total: int):
            self.progress.emit(filename, current, total)

        success = download_model(self.model_id, progress_callback)

        if success:
            from novel_reader.core.model_config import get_model
            model = get_model(self.model_id)
            title = model.title if model else self.model_id
            self.finished.emit(True, f"✅ 模型下载完成: {title}")
        else:
            self.finished.emit(False, f"❌ 模型下载失败: {self.model_id}")


class ModelSettingsDialog(QDialog):
    """TTS 模型设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_chinese_model = "xiao_ya"
        self.current_english_model = "amy"
        self.download_thread: Optional[ModelDownloadThread] = None

        self._init_ui()
        self._load_current_settings()
        self._refresh_model_status()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("TTS 模型设置")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # ==================== 中文模型设置 ====================
        zh_group = QGroupBox("中文模型")
        zh_layout = QVBoxLayout()

        # 中文模型选择
        zh_label_layout = QHBoxLayout()
        zh_label_layout.addWidget(QLabel("当前模型:"))
        self.zh_combo = QComboBox()
        self.zh_combo.currentTextChanged.connect(self._on_chinese_model_changed)
        zh_label_layout.addWidget(self.zh_combo)
        zh_layout.addLayout(zh_label_layout)

        # 中文模型状态
        self.zh_status_label = QLabel()
        self.zh_status_label.setStyleSheet("color: gray;")
        zh_layout.addWidget(self.zh_status_label)

        # 中文模型操作按钮
        zh_btn_layout = QHBoxLayout()
        self.zh_download_btn = QPushButton("下载")
        self.zh_download_btn.clicked.connect(self._download_chinese_model)
        self.zh_delete_btn = QPushButton("删除")
        self.zh_delete_btn.clicked.connect(self._delete_chinese_model)
        zh_btn_layout.addWidget(self.zh_download_btn)
        zh_btn_layout.addWidget(self.zh_delete_btn)
        zh_btn_layout.addStretch()
        zh_layout.addLayout(zh_btn_layout)

        zh_group.setLayout(zh_layout)
        layout.addWidget(zh_group)

        # ==================== 英文模型设置 ====================
        en_group = QGroupBox("英文模型")
        en_layout = QVBoxLayout()

        # 英文模型选择
        en_label_layout = QHBoxLayout()
        en_label_layout.addWidget(QLabel("当前模型:"))
        self.en_combo = QComboBox()
        self.en_combo.currentTextChanged.connect(self._on_english_model_changed)
        en_label_layout.addWidget(self.en_combo)
        en_layout.addLayout(en_label_layout)

        # 英文模型状态
        self.en_status_label = QLabel()
        self.en_status_label.setStyleSheet("color: gray;")
        en_layout.addWidget(self.en_status_label)

        # 英文模型操作按钮
        en_btn_layout = QHBoxLayout()
        self.en_download_btn = QPushButton("下载")
        self.en_download_btn.clicked.connect(self._download_english_model)
        self.en_delete_btn = QPushButton("删除")
        self.en_delete_btn.clicked.connect(self._delete_english_model)
        en_btn_layout.addWidget(self.en_download_btn)
        en_btn_layout.addWidget(self.en_delete_btn)
        en_btn_layout.addStretch()
        en_layout.addLayout(en_btn_layout)

        en_group.setLayout(en_layout)
        layout.addWidget(en_group)

        # ==================== 下载进度 ====================
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # ==================== 所有模型列表 ====================
        list_group = QGroupBox("所有可用模型")
        list_layout = QVBoxLayout()

        self.model_tree = QTreeWidget()
        self.model_tree.setHeaderLabels(["模型", "语言", "大小", "状态"])
        # Set column resize mode
        header = self.model_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        list_layout.addWidget(self.model_tree)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # ==================== 底部按钮 ====================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _load_current_settings(self):
        """加载当前设置"""
        from novel_reader.core import get_setting
        from novel_reader.core.model_config import (
            get_models_by_language, get_model_title
        )

        # 加载中文模型列表
        self.zh_combo.clear()
        zh_models = get_models_by_language("zh")
        for model in zh_models:
            self.zh_combo.addItem(model.title, model.id)

        # 加载英文模型列表
        self.en_combo.clear()
        en_models = get_models_by_language("en")
        for model in en_models:
            self.en_combo.addItem(model.title, model.id)

        # 设置当前选中的模型
        current_zh = get_setting("chinese_model_id", "xiao_ya")
        current_en = get_setting("english_model_id", "amy")

        # 根据 ID 查找并设置
        for i in range(self.zh_combo.count()):
            if self.zh_combo.itemData(i) == current_zh:
                self.zh_combo.setCurrentIndex(i)
                break

        for i in range(self.en_combo.count()):
            if self.en_combo.itemData(i) == current_en:
                self.en_combo.setCurrentIndex(i)
                break

    def _refresh_model_status(self):
        """刷新模型状态"""
        from novel_reader.core.model_config import ALL_MODELS
        from novel_reader.core.model_downloader import get_model_status

        # 刷新下拉框中选中模型的状态
        zh_model_id = self.zh_combo.currentData()
        en_model_id = self.en_combo.currentData()

        zh_status = get_model_status(zh_model_id)
        en_status = get_model_status(en_model_id)

        if zh_status.get("exists"):
            size = zh_status.get("model_size_mb", 0)
            self.zh_status_label.setText(f"✓ 已下载 ({size:.1f} MB)")
            self.zh_status_label.setStyleSheet("color: green;")
            self.zh_download_btn.setEnabled(False)
            self.zh_delete_btn.setEnabled(True)
        else:
            self.zh_status_label.setText(f"✗ 未下载 ({zh_status.get('size_mb', 0)} MB)")
            self.zh_status_label.setStyleSheet("color: orange;")
            self.zh_download_btn.setEnabled(True)
            self.zh_delete_btn.setEnabled(False)

        if en_status.get("exists"):
            size = en_status.get("model_size_mb", 0)
            self.en_status_label.setText(f"✓ 已下载 ({size:.1f} MB)")
            self.en_status_label.setStyleSheet("color: green;")
            self.en_download_btn.setEnabled(False)
            self.en_delete_btn.setEnabled(True)
        else:
            self.en_status_label.setText(f"✗ 未下载 ({en_status.get('size_mb', 0)} MB)")
            self.en_status_label.setStyleSheet("color: orange;")
            self.en_download_btn.setEnabled(True)
            self.en_delete_btn.setEnabled(False)

        # 刷新模型树
        self.model_tree.clear()
        for model in ALL_MODELS:
            status = get_model_status(model.id)
            item = QTreeWidgetItem()
            item.setText(0, model.title)
            item.setText(1, "中文" if model.language == "zh" else "英文")
            item.setText(2, f"{model.size_mb} MB")
            if status.get("exists"):
                item.setText(3, "✓ 已下载")
            else:
                item.setText(3, "✗ 未下载")
            self.model_tree.addTopLevelItem(item)

    def _on_chinese_model_changed(self):
        """中文模型改变"""
        self._refresh_model_status()

    def _on_english_model_changed(self):
        """英文模型改变"""
        self._refresh_model_status()

    def _download_chinese_model(self):
        """下载中文模型"""
        model_id = self.zh_combo.currentData()
        self._start_download(model_id)

    def _download_english_model(self):
        """下载英文模型"""
        model_id = self.en_combo.currentData()
        self._start_download(model_id)

    def _start_download(self, model_id: str):
        """开始下载模型"""
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "警告", "正在下载中，请稍候")
            return

        from novel_reader.core.model_config import get_model
        model = get_model(model_id)
        if not model:
            QMessageBox.warning(self, "错误", f"未找到模型: {model_id}")
            return

        # 禁用按钮
        self.zh_download_btn.setEnabled(False)
        self.en_download_btn.setEnabled(False)

        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setVisible(True)
        self.progress_label.setText(f"正在下载: {model.title}...")

        # 启动下载线程
        self.download_thread = ModelDownloadThread(model_id)
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.start()

    def _on_download_progress(self, filename: str, current: int, total: int):
        """下载进度更新"""
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            mb_current = current / 1024 / 1024
            mb_total = total / 1024 / 1024
            self.progress_label.setText(f"下载中: {filename} ({mb_current:.1f} / {mb_total:.1f} MB)")

    def _on_download_finished(self, success: bool, message: str):
        """下载完成"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # 恢复按钮
        self.zh_download_btn.setEnabled(True)
        self.en_download_btn.setEnabled(True)

        # 刷新状态
        self._refresh_model_status()

        # 显示结果
        if success:
            QMessageBox.information(self, "下载完成", message)
        else:
            QMessageBox.critical(self, "下载失败", message)

    def _delete_chinese_model(self):
        """删除中文模型"""
        model_id = self.zh_combo.currentData()
        self._delete_model(model_id)

    def _delete_english_model(self):
        """删除英文模型"""
        model_id = self.en_combo.currentData()
        self._delete_model(model_id)

    def _delete_model(self, model_id: str):
        """删除模型"""
        from novel_reader.core.model_config import get_model
        from novel_reader.core.model_downloader import delete_model

        model = get_model(model_id)
        if not model:
            QMessageBox.warning(self, "错误", f"未找到模型: {model_id}")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模型吗？\n\n{model.title}\n\n删除后需要重新下载才能使用。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = delete_model(model_id)
            if success:
                QMessageBox.information(self, "删除成功", f"已删除模型: {model.title}")
                self._refresh_model_status()
            else:
                QMessageBox.critical(self, "删除失败", f"删除模型失败: {model.title}")

    def _save_settings(self):
        """保存设置"""
        from novel_reader.core import set_setting, clear_piper_cache

        zh_model_id = self.zh_combo.currentData()
        en_model_id = self.en_combo.currentData()

        set_setting("chinese_model_id", zh_model_id)
        set_setting("english_model_id", en_model_id)

        # 清除 Piper 模型缓存，以便使用新模型
        clear_piper_cache()

        # 检查模型是否已下载
        from novel_reader.core.model_downloader import get_model_status

        zh_status = get_model_status(zh_model_id)
        en_status = get_model_status(en_model_id)

        warnings = []
        if not zh_status.get("exists"):
            warnings.append(f"中文模型 '{zh_status.get('title')}' 未下载")
        if not en_status.get("exists"):
            warnings.append(f"英文模型 '{en_status.get('title')}' 未下载")

        if warnings:
            msg = "设置已保存，但:\n\n" + "\n".join(warnings) + "\n\n请下载模型后才能使用TTS功能。"
            QMessageBox.warning(self, "设置已保存", msg)
        else:
            QMessageBox.information(self, "设置已保存", "TTS 模型设置已保存！")

        self.accept()
