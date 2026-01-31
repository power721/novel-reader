# TTS 模块使用说明

## 安装 Piper

### 方法 1: Python API (推荐)

```bash
pip install piper-tts
```

### 方法 2: 下载二进制文件

下载地址: https://github.com/OHF-Voice/piper1-gpl/releases

将可执行文件放置到 PATH 中，或修改 `PIPER_BIN` 变量指向可执行文件路径。

## 下载 TTS 模型

访问 https://huggingface.co/rhasspy/piper-voices 下载模型。

示例模型：
- 英文: `en_US-lessac-medium` (约 300MB)
- 中文: `zh_CN-huayan-medium` (约 300MB)

将模型文件放置到项目目录，并修改 `tts.py` 中的配置：

```python
PIPER_MODEL = "path/to/model.onnx"
PIPER_CONFIG = "path/to/model.onnx.json"
```

## 使用示例

### 基本使用

```python
from novel_reader.core.tts import text_to_speech

# 转换文本为语音
audio_path = text_to_speech(
    text="Hello, world!",
    output_path="output.wav"
)
```

### 转换书籍 Chunk

```python
from novel_reader.core.tts import convert_chunk

# 转换单个 chunk
audio_path = convert_chunk(
    text="这是要转换的文本内容...",
    book_id=1,
    chunk_id=0
)
# 输出: data/audio/1/chunk_00000.wav
```

### 检查 Piper 是否可用

```python
from novel_reader.core.tts import check_piper_python, check_piper_installed

# 检查 Python API
if check_piper_python():
    print("✓ Piper Python API 可用")

# 检查 CLI 工具
if check_piper_installed():
    print("✓ Piper CLI 可用")
```

## 配置说明

在 `novel_reader/core/tts.py` 文件顶部：

```python
# Piper 可执行文件路径（subprocess 模式）
PIPER_BIN = "piper"

# TTS 模型路径
PIPER_MODEL = "en_US-lessac-medium.onnx"

# 模型配置文件路径
PIPER_CONFIG = "en_US-lessac-medium.onnx.json"

# 音频输出目录
AUDIO_DIR = Path("data/audio")
```

## 工作模式

模块会自动选择最佳方式：

1. **Python API 优先** - 如果安装了 `piper-tts` 包，优先使用 Python API
2. **subprocess 回退** - 如果 Python API 不可用，尝试调用命令行工具

## 注意事项

- 首次转换可能较慢（模型需要加载）
- 音频文件会自动保存到 `data/audio/<book_id>/` 目录
- 确保有足够的磁盘空间存储音频文件
- 中文文本需要使用中文模型
