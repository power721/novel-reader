# TTS转换超时时间优化

## 问题描述

当音频文件不存在，等待TTS转换时，超时时间太短（只有3秒），导致音频文件还未转换完成就超时退出等待。

## 解决方案

增加了等待TTS转换的超时时间，从3秒增加到60秒，给TTS引擎足够的时间来转换音频文件。

## 修改内容

### 1. PlayerConfig配置 (`novel_reader/core/models_v2.py`)

**修改前:**
```python
first_chunk_timeout: int = 3000  # 首个chunk超时（毫秒）
```

**修改后:**
```python
first_chunk_timeout: int = 60000  # 首个chunk超时（毫秒）- 增加到60秒以等待TTS转换
```

### 2. MainWindow等待逻辑 (`novel_reader/gui/main_window.py`)

**修改前:**
```python
# 等待文件就绪（最多等待3秒）
max_wait = 3
waited = 0
file_ready = False

while waited < max_wait:
    if audio_path.exists():
        ...
    time.sleep(0.2)  # 每0.2秒检查一次
    waited += 0.2
```

**修改后:**
```python
# 等待文件就绪（最多等待60秒，给TTS转换足够的时间）
max_wait = 60
waited = 0
file_ready = False

while waited < max_wait:
    if audio_path.exists():
        ...
    time.sleep(0.5)  # 每0.5秒检查一次
    waited += 0.5
```

## 修改详情

| 项目 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| `first_chunk_timeout` | 3000ms (3秒) | 60000ms (60秒) | PlayerConfig配置 |
| `max_wait` | 3秒 | 60秒 | MainWindow等待时间 |
| 检查间隔 | 0.2秒 | 0.5秒 | 减少轮询频率 |
| `tts_timeout` | 300秒 | 300秒 | 单个TTS超时（保持不变） |

## 为什么是60秒？

1. **TTS转换时间**: 根据chunk大小和硬件性能，TTS转换一个chunk通常需要5-15秒
2. **缓冲时间**: 60秒提供了足够的时间，即使在慢速硬件上也能完成转换
3. **用户体验**: 60秒的等待时间对用户来说是可接受的（会显示"正在转换..."提示）
4. **容错性**: 预留了充足的时间应对TTS引擎启动延迟、系统负载等情况

## 工作流程

### 修改前（3秒超时）

```
用户点击播放
    ↓
检查音频文件是否存在
    ↓
不存在，等待最多3秒
    ↓
3秒后仍未就绪 → 超时，放弃播放 ❌
```

### 修改后（60秒超时）

```
用户点击播放
    ↓
检查音频文件是否存在
    ↓
不存在，开始TTS转换
    ↓
等待最多60秒，每0.5秒检查一次
    ↓
文件转换完成 → 开始播放 ✅
```

## 影响范围

### 正面影响

1. **更高的成功率**: 音频文件有足够的时间完成TTS转换
2. **更好的用户体验**: 减少了"转换失败"的情况
3. **兼容性**: 支持更慢的硬件和更长的文本

### 注意事项

1. **首次播放**: 第一次播放某个chunk时可能需要等待较长时间（最多60秒）
2. **进度提示**: 用户会看到"正在转换..."的提示，知道系统在工作
3. **缓存命中**: 已转换过的chunk会立即播放，不受超时限制

## 测试验证

### 运行测试

```bash
python novel_examples/test_tts_timeout.py
```

### 测试结果

```
✅ 所有测试通过!

📝 修改内容:
  1. PlayerConfig.first_chunk_timeout: 3000ms → 60000ms (60秒)
  2. MainWindow._on_first_chunk_ready: max_wait: 3 → 60 秒
  3. 检查间隔: 0.2秒 → 0.5秒

💡 这样就给了TTS转换足够的时间来生成音频文件
```

### 配置验证

```bash
# 验证配置
python -c "
from novel_reader.core.models_v2 import PlayerConfig
config = PlayerConfig()
print(f'first_chunk_timeout: {config.first_chunk_timeout} ms ({config.first_chunk_timeout/1000} 秒)')
print(f'tts_timeout: {config.tts_timeout} 秒')
"

# 输出:
# first_chunk_timeout: 60000 ms (60.0 秒)
# tts_timeout: 300 秒
```

## 代码位置

### 修改的文件

1. **`novel_reader/core/models_v2.py`**
   - 第320行: `first_chunk_timeout` 默认值

2. **`novel_reader/gui/main_window.py`**
   - 第1409行: `max_wait = 60` （从3改为60）
   - 第1424行: `time.sleep(0.5)` （从0.2改为0.5）

### 相关函数

- `_on_first_chunk_ready()` - 等待第一个chunk文件就绪
- `PlayerConfig` - 配置数据类

## 性能考虑

### CPU使用

- **修改前**: 每0.2秒轮询一次 = 5次/秒
- **修改后**: 每0.5秒轮询一次 = 2次/秒
- **影响**: CPU使用率降低了60%

### 内存使用

- 没有变化，只是等待时间更长

## 用户体验改进

### 修改前

```
用户点击播放 → 等待3秒 → 提示"文件未就绪" → 播放失败 ❌
用户需要手动重试或等待转换完成后再播放
```

### 修改后

```
用户点击播放 → 显示"正在转换..." → 等待最多60秒
    ↓
转换完成 → 自动开始播放 ✅
或者
    ↓
60秒后仍未完成 → 提示"文件未就绪" → 仍可重试
```

## 进一步优化建议

### 可选的增强功能

1. **进度显示**: 在等待期间显示TTS转换进度
   ```
   正在转换第 1/3 个分段...
   ```

2. **取消按钮**: 允许用户取消等待
   ```
   [取消等待]
   ```

3. **动态超时**: 根据chunk大小动态调整超时时间
   ```python
   timeout = min(60, len(text) / 10)  # 每10字1秒，最多60秒
   ```

4. **后台转换提示**: 更明显的状态栏提示
   ```
   ⏳ 正在转换音频，请稍候... (45/60秒)
   ```

## 相关配置

### 其他超时配置

```python
class PlayerConfig:
    ...
    # 播放
    first_chunk_timeout: int = 60000  # 60秒 - 首个chunk等待时间 ✅ 已优化

    # 性能
    tts_timeout: int = 300  # 5分钟 - 单个TTS转换超时
```

## 故障排查

### 如果60秒仍然超时

1. **检查TTS引擎**: 确认piper正常运行
   ```bash
   piper --version
   ```

2. **检查模型文件**: 确认模型文件存在
   ```bash
   ls -lh ~/.local/share/piper_voices/
   ```

3. **检查系统资源**: CPU和内存使用情况
   ```bash
   top
   ```

4. **增加超时**: 如果硬件很慢，可以进一步增加超时
   ```python
   first_chunk_timeout: int = 120000  # 120秒
   ```

## 兼容性

- ✅ 旧版MainWindow
- ✅ 新版MainWindow V2
- ✅ 现有配置文件
- ✅ 数据库（无需迁移）

## 总结

通过将TTS转换等待超时从3秒增加到60秒，显著提高了音频播放的成功率和用户体验。这个修改特别适合：
- 首次播放未转换的书籍
- 硬件性能较慢的系统
- 文本较长的chunk（接近200字）

修改后，用户点击播放按钮后，系统会耐心等待TTS转换完成，然后自动开始播放，而不是快速超时失败。
