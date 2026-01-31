# Piper TTS 设置指南

## 问题诊断

运行 TTS 转换时出现以下错误：
```
转换失败: Piper Python API 转换失败: [Errno 2] No such file or directory: 'en_US-lessac-medium.onnx.json'
```

**原因**：Piper TTS 需要下载语音模型文件才能工作。

## 解决方案

### 方案一：使用系统 TTS（推荐）

如果您只是想测试 GUI 功能，可以使用系统自带的 TTS 或跳过 TTS 功能。

### 方案二：安装 Piper TTS（完整功能）

#### 1. 安装 piper-tts

```bash
pip install piper-tts
```

#### 2. 下载语音模型

**英文模型**（推荐）：
```bash
# 创建模型目录
mkdir -p models

# 下载英文模型
cd models
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..
```

**中文模型**：
```bash
# 创建模型目录
mkdir -p models

# 下载中文模型
cd models
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
cd ..
```

#### 3. 更新配置

如果使用中文模型，需要修改配置：

编辑 `novel_reader/core/tts.py`：

```python
# 英文模型
PIPER_MODEL = "en_US-lessac-medium.onnx"
PIPER_CONFIG = "en_US-lessac-medium.onnx.json"

# 或中文模型
PIPER_MODEL = "zh_CN-huayan-medium.onnx"
PIPER_CONFIG = "zh_CN-huayan-medium.onnx.json"
```

#### 4. 验证安装

```bash
python -c "
from novel_reader.core.tts import get_piper_models, find_model_file
print('Available models:')
for model in get_piper_models():
    print(f'  - {model}')
"
```

## 模型搜索路径

Piper TTS 会在以下路径搜索模型文件：

1. 当前目录 (`.`)
2. `models/` 目录
3. `~/.local/share/piper_voices/`
4. `~/piper_models/`

您可以将下载的模型文件放在上述任一目录。

## 快速测试

测试 TTS 是否正常工作：

```python
from novel_reader.core.tts import text_to_speech

# 转换测试
text_to_speech("Hello, this is a test.", "data/audio/test.wav")
print("TTS 转换成功！")
```

## GUI 中使用

1. 启动 GUI：`python -m novel_reader --test`
2. 导入书籍
3. 选择书籍
4. 点击「转换整本书」按钮
5. 查看 TTS 日志和进度

## 常见问题

### Q: 转换速度很慢？

A: Piper TTS 是 CPU 密集型任务，转换速度取决于：
- CPU 性能
- 模型大小（medium 模型比 small 慢，但质量更好）
- 文本长度

### Q: 想使用 GPU 加速？

A: 需要安装支持 GPU 的 piper-tts 版本：
```bash
pip install piper-tts[gpu]
```

### Q: 支持哪些语言？

A: Piper 支持多种语言，查看完整列表：
https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0

## 替代方案

如果不想使用 Piper TTS，可以考虑：

1. **espeak**：轻量级 TTS
   ```bash
   sudo apt install espeak espeak-data
   ```

2. **festival**：另一个开源 TTS
   ```bash
   sudo apt install festival
   ```

3. **在线 API**：调用百度/讯飞等在线 TTS API（需要修改代码）

## 推荐模型

| 语言 | 模型名称 | 大小 | 质量 |
|------|----------|------|------|
| 英文 | en_US-lessac-medium.onnx | ~80MB | 高 |
| 英文 | en_US-lessac-small.onnx | ~30MB | 中 |
| 中文 | zh_CN-huayan-medium.onnx | ~80MB | 高 |
| 中文 | zh_CN-huayan-small.onnx | ~30MB | 中 |

建议下载 **medium** 模型以获得更好的语音质量。
