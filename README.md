# Novel Reader - 本地有声书管理器

一个完全离线的本地有声书管理器，支持文本转语音（TTS）和音频播放。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 特性

- 📚 **多本书管理** - 同时管理多本有声书
- 🎧 **TTS 转换** - 使用 Piper 将文本转为语音（完全离线），支持中英文
- ▶️ **音频播放** - 使用 mpv 播放音频，支持流畅的章节切换
- ⏸️ **暂停/恢复** - 使用 mpv IPC 原生控制，支持即时暂停和恢复
- ⏸️ **断点续播** - 记住每本书的播放进度
- 🔊 **音量控制** - 实时音量调节，自动保存设置
- ⏩ **播放速度** - 支持 0.5x - 2.0x 播放速度，预设常用档位
- ⌨️ **快捷键支持** - 完整的键盘快捷键控制（空格播放/暂停、PageUp/Down 翻章等）
- 🎨 **GUI 界面** - 基于 PySide6 的现代化图形界面
- 🚀 **智能缓存** - LRU 缓存机制，优先级调度，快速首次出声
- 🔄 **分块导航** - 精确到 ~100 字的细粒度导航
- 🌐 **Edge TTS 支持** - 支持 Microsoft Edge TTS 在线语音（可选）
- 💾 **本地存储** - SQLite 数据库，所有数据本地保存
- 📴 **完全离线** - Piper TTS 无需网络连接
- 🗑️ **自动清理** - 自动清理旧音频文件，节省存储空间

## 系统要求

- **操作系统**: Linux（推荐），macOS，或其他 Unix-like 系统
- **Python**: 3.11
- **依赖程序**:
  - `mpv` - 音频播放器（必需）
  - `ffmpeg` - 音频转换工具（可选，Edge TTS 需要）
  - `piper-tts` - 离线 TTS 引擎（可选，通过 pip 安装）

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/power721/novel-reader
cd novel-reader
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装系统依赖

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install mpv ffmpeg
```

#### Arch Linux

```bash
sudo pacman -S mpv ffmpeg
```

#### macOS

```bash
brew install mpv ffmpeg
```

**说明**：
- `mpv` 是必需的，用于音频播放
- `ffmpeg` 是可选的，仅在需要使用 Edge TTS 时需要（用于 MP3 到 WAV 转换）

### 4. 下载 TTS 模型

#### 方式一：使用脚本下载（推荐）

使用提供的脚本快速下载推荐模型：

```bash
./download_piper_model.sh
```

脚本支持以下模型：
- **英文**: lessac (medium/small), amy (medium)
- **中文**: 花檐/小雅/朝文 (medium/small)

#### 方式二：通过 GUI 管理

首次运行程序时，可以通过 **设置 -> TTS 模型设置** 对话框：

1. 选择需要的中英文模型
2. 点击"下载"按钮下载模型
3. 下载完成后保存设置

#### 可用模型列表

**中文模型**：
- `xiao_ya` (小雅) - 默认中文模型，约 60MB
- `huayan` (花檐) - 约 60MB
- `chaowen` (潮文) - 约 60MB

**英文模型**：
- `amy` - 默认英文模型，约 60MB
- `lessac` - 约 60MB
- `alan` (英式英语) - 约 60MB

模型会下载到 `models/` 目录，首次运行时自动复制到用户数据目录。

### 5. 配置

首次运行会自动创建配置文件和数据库：

```bash
python -m novel_reader
```

配置文件位置：`~/.config/novel-reader/config.json`

## 使用方法

### 启动程序

```bash
# 启动 GUI
python -m novel_reader

# 启动 GUI 并创建测试数据
python -m novel_reader --test
```

### 主要功能

1. **导入书籍** - 支持导入 TXT、EPUB、MOBI、AZW3 等格式的文本文件
2. **自动分章** - 智能识别章节标题并分割
3. **分块导航** - 精确到 ~100 字的细粒度导航
4. **智能缓存** - 优先级调度，快速首次出声（0.1-0.3s）
5. **流畅播放** - 后台预合成，自动播放下一章
6. **即时暂停** - 使用 mpv IPC 原生控制，支持即时暂停和恢复播放
7. **进度管理** - 自动保存播放位置，支持断点续播
8. **书签** - 在任意位置添加书签
9. **音量控制** - 实时调节播放音量（0% - 100%），设置自动保存
10. **播放速度** - 调节播放速度（0.5x - 2.0x），支持预设档位（0.5x, 1.0x, 1.25x, 1.5x, 2.0x）
11. **快捷键控制** - 完整的键盘快捷键支持，无需鼠标即可控制播放
12. **自动清理** - 自动清理旧音频文件，节省存储空间

### GUI 界面

- **书籍列表** - 查看和管理所有导入的书籍
- **章节列表** - 浏览和跳转到任意章节
- **播放器** - 统一的播放/暂停按钮、章节导航、分段导航、进度显示、文本高亮、音量和速度调节
- **设置** - 配置 TTS 模型、音频参数等

### 键盘快捷键

Novel Reader 支持完整的键盘快捷键控制：

| 快捷键 | 功能 |
|--------|------|
| `空格` | 播放 / 暂停 |
| `Escape` | 停止播放 |
| `← / →` | 后退 / 前进一个分段 |
| `PageUp / PageDown` | 上一章 / 下一章 |
| `↑ / ↓` | 增加 / 减少音量 |
| `Ctrl + I` | 导入书籍 |
| `F5` | 刷新列表 |
| `F1` | 显示快捷键帮助 |

**提示**：按 `F1` 可随时查看完整的快捷键列表。

### TTS 选项

- **Piper TTS** (默认) - 完全离线，支持中英文
- **Edge TTS** (可选) - Microsoft Edge TTS 在线语音，支持多种中英文音色，需要安装 ffmpeg

#### 模型管理

程序支持完整的模型管理功能：

1. **模型选择** - 分别设置中文和英文 TTS 模型
2. **下载管理** - 通过 GUI 下载和删除模型
3. **进度显示** - 实时显示下载进度
4. **状态检查** - 查看所有可用模型的下载状态
5. **模型切换** - 切换模型后自动清理缓存

所有模型文件存储在 `~/.local/share/novel-reader/models/` 或 `models/` 目录。

## 目录结构

```
novel-reader/
├── novel_reader/           # 主程序包
│   ├── __main__.py        # 程序入口
│   ├── gui/               # PySide6 GUI
│   │   ├── pyside_main.py      # GUI 入口
│   │   ├── main_window.py      # 主窗口
│   │   ├── widgets/            # UI 组件
│   │   ├── workers/            # 后台线程
│   │   ├── dialogs/            # 对话框
│   │   └── controllers/        # 控制器适配器
│   ├── ui/                 # TUI 界面（遗留）
│   ├── core/               # 核心逻辑（v2 架构）
│   │   ├── models_v2.py        # 数据模型
│   │   ├── playback_controller_v2.py  # 播放控制器
│   │   ├── chunk_manager_v2.py       # 文本分块
│   │   ├── tts_scheduler_v2.py       # TTS 调度
│   │   ├── audio_cache.py            # LRU 缓存
│   │   ├── audio_player_v2.py        # 音频播放
│   │   ├── model_config.py           # TTS 模型配置
│   │   ├── model_downloader.py       # 模型下载管理
│   │   ├── settings.py               # 配置管理
│   │   ├── tts.py                    # TTS 核心引擎
│   │   └── sentence_manager.py       # 句子处理
│   ├── models/             # 数据库模型
│   └── utils/              # 工具函数
├── tests/                  # 测试
├── docs/                   # 文档
├── g2pW/                   # 中文转拼音工具
├── requirements.txt        # Python 依赖
├── download_piper_model.sh # TTS 模型下载脚本
└── README.md               # 本文件
```

## 配置

编辑配置文件 `~/.config/novel-reader/config.json`：

```json
{
  "tts_engine": "piper",
  "tts_model": "lessac-medium",
  "tts_voice": "en_US-lessac-medium.onnx",
  "audio_cache_size": 80,
  "text_chunk_size": 100,
  "prefetch_chunks": 2,
  "volume": 1.0,
  "playback_speed": 100
}
```

### 配置参数说明

| 参数 | 说明               | 默认值       |
|------|------------------|-----------|
| `auto_play_on_startup` | 启动时自动播放          | `true`    |
| `auto_play_on_book_select` | 选择书籍时自动播放        | `false`   |
| `remember_last_book` | 记住最后选择的书籍        | `true`    |
| `auto_play_next_book` | 自动播放下一本书         | `false`   |
| `auto_play_next_chapter` | 自动播放下一章节         | `true`    |
| `chinese_model_id` | 中文 TTS 模型 ID     | `xiao_ya` |
| `english_model_id` | 英文 TTS 模型 ID     | `amy`     |
| `model_dir` | 模型存储目录           | `models`  |
| `prefetch_chunk_count` | 预转换后续 chunk 数量   | `3`       |
| `cleanup_old_chunk_threshold` | 清理 N 之前的音频文件     | `50`      |
| `audio_cache_size` | 缓存 chunk 数量      | `80`      |
| `text_chunk_size` | 每个 chunk 字符数     | `100`     |
| `prefetch_chunks` | 预取 chunk 数量      | `2`       |
| `volume` | 播放音量 (0.0 - 1.0) | `1.0`     |
| `playback_speed` | 播放速度 (50 - 200)  | `100`     |

## 数据存储

- **配置**: `~/.config/novel-reader/config.json`
- **数据库**: `~/.local/share/novel-reader/library.db`
- **音频**: `~/.local/share/novel-reader/audio/`
- **TTS 模型**: `~/.local/share/novel-reader/models/`

## 故障排除

### TTS 转换失败

- 确认 `piper-tts` 已安装: `python -c "import piper_tts"`
- 使用 `./download_piper_model.sh` 下载 TTS 模型
- 或通过 GUI 界面下载模型（设置 -> TTS 模型设置）
- 检查模型文件是否在 `~/.local/share/novel-reader/models/` 或 `models/`
- 确认配置文件中的模型 ID 正确：`chinese_model_id` 和 `english_model_id`
- 查看日志: `~/.cache/novel-reader/logs/`

### 模型下载失败

- 检查网络连接（或使用 HuggingFace 镜像）
- 确认磁盘空间充足（每个模型约 60MB）
- 尝试手动从 HuggingFace 下载模型文件
- 检查模型目录的写入权限

### 音频播放失败

- 确认 mpv 已正确安装: `mpv --version`
- 检查音频设备是否正常工作
- 尝试使用 `mpv <audio_file>` 直接播放测试

### Edge TTS 转换失败

- 确认 ffmpeg 已正确安装: `ffmpeg --version`
- Edge TTS 需要使用 ffmpeg 将 MP3 转换为 WAV 格式
- 检查网络连接（Edge TTS 需要在线访问 Microsoft 服务器）
- 尝试切换到 Piper TTS（完全离线）

### 中文支持

项目内置中文支持，包括：
- 自动繁简转换
- 拼音转换（用于多音字处理）
- 数字/标点符号朗读优化

使用 `./download_piper_model.sh` 下载中文模型（花檐、小雅、朝文）。

## 架构

Novel Reader 采用模块化的 v2 架构：

- **Chunk-based** - 文本被分割成 ~100 字的 chunk 作为最小逻辑单元
- **优先级调度** - 当前播放 chunk 获得最高 TTS 优先级（URGENT > HIGH > NORMAL > LOW）
- **LRU 缓存** - 智能缓存策略，避免重复 TTS 转换
- **状态机** - 清晰的播放状态管理（IDLE, LOADING, READY, PLAYING, PAUSED）
- **IPC 控制** - 通过 mpv IPC socket 实现即时暂停/恢复、音量和速度调节
- **模型管理** - 支持多个 Piper 模型，支持中英文自动切换
- **音频清理** - 自动清理旧的音频文件，节省存储空间

详细架构文档请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 音频清理

为了节省存储空间，Novel Reader 实现了自动清理机制：

### 工作原理

- **触发时机**：每次播放完一个 chunk 后自动触发清理
- **清理规则**：删除 `当前chunk索引 - 阈值` 之前的所有音频文件
- **默认阈值**：50（保留最近播放的 50 个 chunk 的音频）

### 配置选项

通过配置文件 `~/.config/novel-reader/config.json` 调整清理阈值：

```json
{
  "cleanup_old_chunk_threshold": 50
}
```

### 示例

假设当前正在播放 chunk N，清理阈值为 50：

- **保留**：chunk N-50 到 N 的音频文件
- **删除**：chunk 0 到 N-51 的音频文件

### 注意事项

- 清理操作不会影响当前播放和预取的音频
- 删除的音频文件可以随时重新生成（TTS 转换）
- 设置较小的阈值可以节省更多空间，但可能需要重新生成音频

### 手动清理

如果需要手动清理所有音频文件：

```bash
# 删除指定书籍的所有音频
rm -rf ~/.local/share/novel-reader/audio/<book_id>/
```

## 模型管理

### Piper 模型

Novel Reader 使用 Piper TTS 引擎进行离线文本转语音，支持以下特性：

- **中英文混合** - 自动检测文本语言并使用相应模型
- **多音色支持** - 提供多个中文和英文音色供选择
- **模型缓存** - Python API 模式下自动缓存加载的模型
- **热切换** - 切换模型时自动清理缓存并重新加载

### 模型文件结构

每个模型包含两个文件：
- `{model_name}.onnx` - 模型权重文件
- `{model_name}.onnx.json` - 模型配置文件

示例：
```
models/
├── zh_CN-xiao_ya-medium.onnx
├── zh_CN-xiao_ya-medium.onnx.json
├── en_US-amy-medium.onnx
└── en_US-amy-medium.onnx.json
```

### 模型搜索路径

程序按以下顺序搜索模型文件：
1. `models/` - 当前项目目录
2. `~/.local/share/piper_voices/` - 用户数据目录
3. `~/piper_models/` - 用户主目录
4. 当前目录

### 模型配置

模型配置定义在 `novel_reader/core/model_config.py` 中，包含：

- 模型唯一标识符 (ID)
- 显示名称（中英文）
- 语言代码 (zh/en)
- HuggingFace 下载地址
- 文件大小信息

可以通过修改此文件添加新的模型支持。

## 打包为可执行程序

### 快速打包

使用提供的打包脚本将程序打包为独立的可执行文件：

```bash
# 安装打包工具
pip install pyinstaller

# 运行打包脚本
./build.sh
```

打包完成后，在 `dist/` 目录会生成：

```
dist/
├── novel-reader                          # 可执行文件
├── novel-reader-linux/                   # 发布目录
│   ├── novel-reader                      # 可执行文件
│   ├── start.sh                          # 启动脚本
│   ├── README.txt                        # 用户说明
│   └── INSTALL.md                        # 安装指南
└── novel-reader-YYYYMMDD-linux-x86_64.tar.gz  # 压缩包
```

### 系统要求

打包后的程序在目标系统上需要：

- **mpv 播放器**（必需）: `sudo apt install mpv`
- **TTS 模型**（可选）: 首次运行时下载

### 分发

将压缩包发送给用户：

```bash
# 用户解压
tar -xzf novel-reader-YYYYMMDD-linux-x86_64.tar.gz
cd novel-reader-linux

# 安装系统依赖
sudo apt install mpv

# 运行程序
./start.sh
```

### 更多信息

详细的打包指南请参考 [docs/BUILD.md](docs/BUILD.md)。

## 开发

```bash
# 代码格式化（需先安装 black）
black novel_reader/

# 运行示例测试
python -m novel_examples.test_new_arch
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [PySide6](https://wiki.qt.io/Qt_for_Python) - GUI 框架
- [Piper](https://github.com/rhasspy/piper) - 快速离线 TTS
- [Edge TTS](https://github.com/rany2/edge-tts) - Microsoft 在线 TTS（可选）
- [mpv](https://mpv.io/) - 媒体播放器
- [g2pW](https://github.com/Gregorius/pinyin-g2pW) - 中文转拼音
- [sentence-stream](https://github.com/jjlee/sentence-stream) - 句子分割
