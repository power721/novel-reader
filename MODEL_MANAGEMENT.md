# Piper TTS 模型管理功能

## 概述

Novel Reader 现在支持完整的 Piper TTS 模型管理功能，包括：
- 多模型选择（中文/英文）
- 图形化模型管理界面
- 自动下载模型
- 音频文件名包含模型 ID

## 可用模型

### 中文模型

| ID | 名称 | 大小 |
|---|---|---|
| `xiao_ya` | 小雅 (Xiao Ya) - 中 | ~176 MB |
| `xiao_ya_low` | 小雅 (Xiao Ya) - 低 | ~44 MB |
| `huayan` | 花檐 (Hua Yan) - 中 | ~176 MB |
| `huayan_low` | 花檐 (Hua Yan) - 低 | ~44 MB |
| `chaowen` | 潮文 (Chao Wen) - 中 | ~176 MB |
| `chaowen_low` | 潮文 (Chao Wen) - 低 | ~44 MB |

### 英文模型

| ID | 名称 | 大小 |
|---|---|---|
| `amy` | Amy - 中 | ~587 MB |
| `amy_low` | Amy - 低 | ~184 MB |
| `lessac` | Lessac - 中 | ~587 MB |
| `lessac_low` | Lessac - 低 | ~184 MB |
| `danny` | Danny - 中 (英式) | ~587 MB |
| `danny_low` | Danny - 低 (英式) | ~184 MB |

默认模型：
- 中文：`xiao_ya`
- 英文：`amy`

## 使用方法

### 通过 GUI 管理模型

1. 打开 Novel Reader
2. 点击菜单 **设置 → TTS 模型管理**
3. 在对话框中：
   - 选择想要使用的中文/英文模型
   - 点击"下载"按钮下载未安装的模型
   - 点击"删除"按钮卸载不需要的模型
   - 点击"保存"保存设置

### 通过命令行管理模型

```python
from novel_reader.core import (
    get_available_models,
    get_model_status,
    download_model,
    delete_model
)

# 查看已下载的模型
available = get_available_models()
for model in available:
    print(f"{model.id}: {model.title}")

# 查看模型状态
status = get_model_status("xiao_ya")
print(f"已下载: {status['exists']}")
print(f"大小: {status.get('model_size_mb', 0)} MB")

# 下载模型
download_model("xiao_ya")

# 删除模型
delete_model("xiao_ya")
```

## 音频文件命名

新的音频文件命名格式包含模型 ID：

```
chunk_{model_id}_{chunk_id:05d}.wav
```

示例：
- `chunk_xiao_ya_00100.wav` - 使用小雅模型生成的第100个分段
- `chunk_amy_00200.wav` - 使用 Amy 模型生成的第200个分段

## 配置文件

设置保存在 `data/settings.json`：

```json
{
  "chinese_model_id": "xiao_ya",
  "english_model_id": "amy",
  "model_dir": "models"
}
```

## 模型存储位置

模型默认存储在以下位置（按优先级）：
1. `./models/` (项目根目录)
2. `~/.local/share/piper_voices/`
3. `~/piper_models/`

## 开发者信息

### 核心模块

- `novel_reader/core/model_config.py` - 模型定义和查询
- `novel_reader/core/model_downloader.py` - 模型下载管理
- `novel_reader/gui/dialogs/model_settings_dialog.py` - GUI 管理界面

### API 示例

```python
from novel_reader.core.model_config import (
    get_model,
    get_models_by_language,
    get_default_model
)

# 获取模型信息
model = get_model("xiao_ya")
print(f"标题: {model.title}")
print(f"语言: {model.language}")
print(f"大小: {model.size_mb} MB")
print(f"文件名: {model.model_name}")

# 获取所有中文模型
zh_models = get_models_by_language("zh")

# 获取默认模型
default_zh = get_default_model("zh")
```

## 测试

运行测试脚本验证功能：

```bash
python test_model_config.py
```

## 注意事项

1. **首次使用**: 首次使用前需要先下载模型文件
2. **模型大小**: 中等质量模型约 176-587 MB，低质量约 44-184 MB
3. **网络**: 模型从 HuggingFace 下载，中国用户会自动使用镜像站
4. **兼容性**: 旧的音频文件（不包含 model_id）仍可使用，但建议重新生成

## 未来改进

- [ ] 模型质量对比功能
- [ ] 自定义语音参数（音调、语速）
- [ ] 批量下载多个模型
- [ ] 模型缓存清理
- [ ] 语音样本预览
