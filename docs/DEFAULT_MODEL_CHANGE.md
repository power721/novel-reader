# 默认模型更改说明

## 变更内容

默认 TTS 模型已从英文模型更改为**中文模型**。

### 之前配置
```python
PIPER_MODEL = "en_US-lessac-medium.onnx"
PIPER_CONFIG = "en_US-lessac-medium.onnx.json"
```

### 当前配置
```python
PIPER_MODEL = "zh_CN-huayan-medium.onnx"
PIPER_CONFIG = "zh_CN-huayan-medium.onnx.json"
```

## 验证结果

```bash
============================================================
默认模型配置验证
============================================================

默认模型: zh_CN-huayan-medium.onnx
默认配置: zh_CN-huayan-medium.onnx.json

模型文件: ✓ 找到
  路径: models/zh_CN-huayan-medium.onnx

配置文件: ✓ 找到
  路径: models/zh_CN-huayan-medium.onnx.json

测试 TTS 转换:
✓ 转换成功: data/audio/default_model_test.wav
✓ 文件大小: 144428 bytes

🎉 默认中文模型配置成功！
```

## 自动回退机制

如果默认模型未找到，系统会自动使用搜索路径中找到的第一个可用模型。

### 搜索路径
1. `.` - 当前目录
2. `models/` - models 目录
3. `~/.local/share/piper_voices/` - Linux 用户目录
4. `~/piper_models/` - 用户主目录

## 如何使用其他模型

如果您想使用其他模型（如英文模型），有两种方式：

### 方式一：修改配置文件

编辑 `novel_reader/core/tts.py`：

```python
# 使用英文模型
PIPER_MODEL = "en_US-lessac-medium.onnx"
PIPER_CONFIG = "en_US-lessac-medium.onnx.json"
```

### 方式二：在代码中指定

```python
from novel_reader.core.tts import text_to_speech

# 使用英文模型
output = text_to_speech(
    "Hello, world!",
    "output.wav",
    model="en_US-lessac-medium.onnx",
    config="en_US-lessac-medium.onnx.json"
)
```

## 支持的语言

| 语言 | 模型名称 |
|------|----------|
| 中文（默认）| zh_CN-huayan-medium.onnx |
| 英文 | en_US-lessac-medium.onnx |
| 英文（轻量）| en_US-lessac-small.onnx |

模型下载地址：https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0

## 完整测试

```bash
# 测试默认模型配置
python -c "
from novel_reader.core.tts import text_to_speech
text_to_speech('你好，世界！', 'test.wav')
print('转换成功')
"

# 运行 GUI
python -m novel_reader --test
```

## 注意事项

1. **自动回退**：即使默认模型未找到，系统也会自动使用其他可用模型
2. **中文优先**：默认配置针对中文内容优化
3. **英文内容**：中文模型也可以朗读英文，效果可能不如专用英文模型
