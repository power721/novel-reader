# 更新总结 - 2025-01-31

## 修复的问题

### 1. TTS 模块变量名拼写错误
**文件**: `novel_reader/core/tts.py`

修复了两处拼写错误：
- `_PIPER_PYPER_AVAILABLE` → `_PIPER_PYTHON_AVAILABLE`
- `_PIPER_PYERN_AVAILABLE` → `_PIPER_PYTHON_AVAILABLE`

### 2. TTS 模型文件查找优化
**文件**: `novel_reader/core/tts.py`

**新增功能**：
- `find_model_file()` - 在多个路径中查找模型文件
- `get_piper_models()` - 列出所有可用的模型文件
- 更详细的错误提示，包含设置指南

**模型搜索路径**：
- `.` - 当前目录
- `models/` - models 目录
- `~/.local/share/piper_voices/` - Linux 用户目录
- `~/piper_models/` - 用户主目录

### 3. 播放前音频文件检查
**文件**: `novel_reader/core/player.py`, `novel_reader/gui/main_window.py`

- 播放器现在会在开始播放前检查是否有可用的音频文件
- 如果没有音频文件，会显示友好的错误提示
- 显示可用音频文件数量

### 4. GUI 智能转换提示
**文件**: `novel_reader/gui/main_window.py`

**改进**：
- 点击播放按钮时，如果未转换，自动提示并开始转换
- 点击章节时自动触发 TTS 转换（无需确认）
- 双击章节时，如果未转换，自动开始转换

### 5. 移除 TUI 支持
**文件**: `novel_reader/__main__.py`, `requirements.txt`

- 移除 TUI 相关代码
- 移除 `textual` 和 `rich` 依赖
- PySide6 GUI 成为唯一的用户界面

## 新增文件

### 文档
- `docs/PIPER_SETUP.md` - Piper TTS 设置指南
- `docs/UPDATE_LOG.md` - 更新日志

### 脚本
- `test_piper.py` - Piper TTS 配置测试脚本
- `download_piper_model.sh` - 模型下载脚本
- `test_gui.py` - GUI 功能测试脚本

## 使用方法

### 安装依赖
```bash
pip install -r requirements.txt
```

### 下载 Piper 模型（可选）
```bash
chmod +x download_piper_model.sh
./download_piper_model.sh
```

### 测试配置
```bash
# 测试 Piper 配置
python test_piper.py

# 测试 GUI
python test_gui.py
```

### 运行程序
```bash
# 运行 GUI
python -m novel_reader

# 运行 GUI 并创建测试数据
python -m novel_reader --test
```

## 工作流程

### 推荐的使用流程
1. **启动程序**: `python -m novel_reader --test`
2. **导入书籍**: 拖拽 `.txt` 文件到窗口
3. **选择书籍**: 点击书籍查看章节
4. **自动转换**: 点击任意章节自动触发 TTS 转换
5. **查看进度**: 在 TTS 日志中查看转换进度
6. **播放音频**: 转换完成后双击章节播放

### TTS 转换提示
- 点击章节 → 自动开始 TTS 转换（无需确认）
- 双击章节（未转换）→ 自动开始转换
- 双击章节（已转换）→ 开始播放
- 点击「转换整本书」→ 手动触发转换

## 依赖项

### 必需
- `PySide6>=6.6.0` - Qt for Python GUI 框架

### 可选
- `piper-tts>=1.2.0` - TTS 转换（需要下载模型文件）
- `mpv` - 音频播放器（系统包，`sudo apt install mpv`）

## 已知问题

### TTS 模型文件未找到
**错误信息**:
```
转换失败: Piper Python API 转换失败: [Errno 2] No such file or directory: 'en_US-lessac-medium.onnx.json'
```

**解决方案**:
1. 下载 Piper 模型文件
2. 运行 `./download_piper_model.sh` 选择模型
3. 或参考 `docs/PIPER_SETUP.md` 手动下载

## 测试结果

```bash
$ python test_piper.py
============================================================
Piper TTS 配置测试
============================================================

测试 1: 检查 piper-tts 安装
✓ piper-tts 已安装

测试 2: 检查模型文件
✗ 模型文件未找到 (需下载)

测试 3: 测试 TTS 转换
✗ TTS 转换失败 (需模型文件)

测试 4: 检查 mpv 播放器
✓ mpv 已安装

总计: 2/4 通过
```

**说明**：模型文件需要单独下载，这是正常的。使用 `download_piper_model.sh` 脚本可以快速下载。

## 下一步

1. **下载模型**: 运行 `./download_piper_model.sh`
2. **验证配置**: 运行 `python test_piper.py`
3. **测试转换**: 在 GUI 中导入书籍并测试 TTS 转换
4. **享受阅读**: 转换完成后即可播放音频
