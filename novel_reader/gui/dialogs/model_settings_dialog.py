"""
TTS 语音设置对话框

用于选择和管理 Edge TTS 语音设置
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox,
    QMessageBox, QSpinBox
)
from typing import Optional
from novel_reader.core import set_setting, get_setting


class ModelSettingsDialog(QDialog):
    """TTS 语音设置对话框 (Edge TTS)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("TTS 语音设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # ==================== Edge TTS 语音设置 ====================
        voice_group = QGroupBox("Edge TTS 语音 (微软在线神经网络语音)")
        voice_layout = QVBoxLayout()

        # 中文语音设置
        zh_edge_group = QGroupBox("中文语音")
        zh_edge_layout = QVBoxLayout()

        zh_label_layout = QHBoxLayout()
        zh_label_layout.addWidget(QLabel("选择语音:"))
        self.edge_zh_combo = QComboBox()
        self.edge_zh_combo.currentTextChanged.connect(self._on_edge_voice_changed)
        zh_label_layout.addWidget(self.edge_zh_combo)
        zh_edge_layout.addLayout(zh_label_layout)

        self.edge_zh_desc_label = QLabel()
        self.edge_zh_desc_label.setWordWrap(True)
        self.edge_zh_desc_label.setStyleSheet("color: gray; font-size: 11px;")
        zh_edge_layout.addWidget(self.edge_zh_desc_label)

        zh_edge_group.setLayout(zh_edge_layout)
        voice_layout.addWidget(zh_edge_group)

        # 英文语音设置
        en_edge_group = QGroupBox("英文语音")
        en_edge_layout = QVBoxLayout()

        en_label_layout = QHBoxLayout()
        en_label_layout.addWidget(QLabel("选择语音:"))
        self.edge_en_combo = QComboBox()
        self.edge_en_combo.currentTextChanged.connect(self._on_edge_voice_changed)
        en_label_layout.addWidget(self.edge_en_combo)
        en_edge_layout.addLayout(en_label_layout)

        self.edge_en_desc_label = QLabel()
        self.edge_en_desc_label.setWordWrap(True)
        self.edge_en_desc_label.setStyleSheet("color: gray; font-size: 11px;")
        en_edge_layout.addWidget(self.edge_en_desc_label)

        en_edge_group.setLayout(en_edge_layout)
        voice_layout.addWidget(en_edge_group)

        # Edge TTS 参数设置
        params_group = QGroupBox("语音参数调整")
        params_layout = QVBoxLayout()

        # 语速
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("语速:"))
        self.edge_rate_spin = QSpinBox()
        self.edge_rate_spin.setRange(-50, 100)
        self.edge_rate_spin.setValue(0)
        self.edge_rate_spin.setSuffix("%")
        self.edge_rate_spin.setPrefix("+")
        rate_layout.addWidget(self.edge_rate_spin)
        rate_layout.addStretch()
        params_layout.addLayout(rate_layout)

        # 音调
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("音调:"))
        self.edge_pitch_spin = QSpinBox()
        self.edge_pitch_spin.setRange(-50, 50)
        self.edge_pitch_spin.setValue(0)
        self.edge_pitch_spin.setSuffix("Hz")
        self.edge_pitch_spin.setPrefix("+")
        pitch_layout.addWidget(self.edge_pitch_spin)
        pitch_layout.addStretch()
        params_layout.addLayout(pitch_layout)

        # 音量
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.edge_volume_spin = QSpinBox()
        self.edge_volume_spin.setRange(-100, 100)
        self.edge_volume_spin.setValue(0)
        self.edge_volume_spin.setSuffix("%")
        self.edge_volume_spin.setPrefix("+")
        volume_layout.addWidget(self.edge_volume_spin)
        volume_layout.addStretch()
        params_layout.addLayout(volume_layout)

        params_group.setLayout(params_layout)
        voice_layout.addWidget(params_group)

        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        # ==================== Edge TTS 状态 ====================
        self.edge_status_group = QGroupBox("Edge TTS 状态")
        edge_status_layout = QVBoxLayout()
        self.edge_status_label = QLabel()
        self.edge_status_label.setWordWrap(True)
        edge_status_layout.addWidget(self.edge_status_label)
        self.edge_status_group.setLayout(edge_status_layout)
        layout.addWidget(self.edge_status_group)

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
        # 加载 Edge TTS 语音列表
        self._load_edge_voices()

        # 加载 Edge TTS 参数
        rate_str = get_setting("edge_rate", "+0%")
        pitch_str = get_setting("edge_pitch", "+0Hz")
        volume_str = get_setting("edge_volume", "+0%")

        try:
            rate_val = int(rate_str.replace('%', '').replace('+', ''))
            self.edge_rate_spin.setValue(rate_val)
        except:
            pass

        try:
            pitch_val = int(pitch_str.replace('Hz', '').replace('+', ''))
            self.edge_pitch_spin.setValue(pitch_val)
        except:
            pass

        try:
            volume_val = int(volume_str.replace('%', '').replace('+', ''))
            self.edge_volume_spin.setValue(volume_val)
        except:
            pass

    def _load_edge_voices(self):
        """加载 Edge TTS 语音列表"""
        from novel_reader.core.edge_tts_config import get_voices_by_language

        # 加载中文语音列表
        self.edge_zh_combo.clear()
        zh_voices = get_voices_by_language("zh")
        for voice in zh_voices:
            self.edge_zh_combo.addItem(f"{voice.title} ({voice.gender})", voice.id)

        # 加载英文语音列表
        self.edge_en_combo.clear()
        en_voices = get_voices_by_language("en")
        for voice in en_voices:
            self.edge_en_combo.addItem(f"{voice.title} ({voice.gender})", voice.id)

        # 设置当前选中的语音
        current_zh_voice = get_setting("edge_chinese_voice_id", "xiaoxiao")
        current_en_voice = get_setting("edge_english_voice_id", "jenny")

        from novel_reader.core.edge_tts_config import get_voice

        # 验证语音 ID 是否有效
        valid_voice_ids = [v.id for v in zh_voices]
        if current_zh_voice not in valid_voice_ids:
            current_zh_voice = "xiaoxiao"
            set_setting("edge_chinese_voice_id", current_zh_voice)

        for i in range(self.edge_zh_combo.count()):
            if self.edge_zh_combo.itemData(i) == current_zh_voice:
                self.edge_zh_combo.setCurrentIndex(i)
                break

        valid_en_voice_ids = [v.id for v in en_voices]
        if current_en_voice not in valid_en_voice_ids:
            current_en_voice = "jenny"
            set_setting("edge_english_voice_id", current_en_voice)

        for i in range(self.edge_en_combo.count()):
            if self.edge_en_combo.itemData(i) == current_en_voice:
                self.edge_en_combo.setCurrentIndex(i)
                break

        self._update_edge_voice_descriptions()
        self._refresh_edge_status()

    def _on_edge_voice_changed(self, voice_name: str):
        """Edge TTS 语音改变事件"""
        self._update_edge_voice_descriptions()

    def _update_edge_voice_descriptions(self):
        """更新 Edge TTS 语音描述"""
        from novel_reader.core.edge_tts_config import get_voice

        zh_voice_id = self.edge_zh_combo.currentData()
        zh_voice = get_voice(zh_voice_id)
        if zh_voice:
            self.edge_zh_desc_label.setText(
                f"{zh_voice.description} | 语言: {zh_voice.locale}"
            )

        en_voice_id = self.edge_en_combo.currentData()
        en_voice = get_voice(en_voice_id)
        if en_voice:
            self.edge_en_desc_label.setText(
                f"{en_voice.description} | 语言: {en_voice.locale}"
            )

    def _refresh_edge_status(self):
        """刷新 Edge TTS 状态"""
        from novel_reader.core.edge_tts import check_edge_tts_available

        is_available = check_edge_tts_available()

        if is_available:
            self.edge_status_label.setText(
                "<span style='color: green;'>✓ Edge TTS 可用</span><br>"
                "Edge TTS 使用微软在线语音服务，无需下载模型。"
            )
            self.edge_status_label.setStyleSheet("")
        else:
            self.edge_status_label.setText(
                "<span style='color: red;'>✗ Edge TTS 不可用</span><br>"
                "请安装 edge-tts 库：<br>"
                "<code>pip install edge-tts</code>"
            )

    def _save_settings(self):
        """保存设置"""
        from novel_reader.core import set_settings
        from novel_reader.core.edge_tts_config import get_voice

        updates = {}

        zh_voice_id = self.edge_zh_combo.currentData()
        en_voice_id = self.edge_en_combo.currentData()

        updates["edge_chinese_voice_id"] = zh_voice_id
        updates["edge_english_voice_id"] = en_voice_id

        # 保存 Edge TTS 参数
        rate_val = self.edge_rate_spin.value()
        pitch_val = self.edge_pitch_spin.value()
        volume_val = self.edge_volume_spin.value()

        updates["edge_rate"] = f"+{rate_val}%"
        updates["edge_pitch"] = f"+{pitch_val}Hz"
        updates["edge_volume"] = f"+{volume_val}%"

        set_settings(updates)

        QMessageBox.information(self, "设置已保存", "Edge TTS 语音设置已保存！")
        self.accept()
