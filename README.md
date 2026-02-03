# Novel Reader - 本地有声书管理器

一个完全离线的本地有声书管理器，支持文本转语音（TTS）和音频播放。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 特性

- 📚 **多本书管理** - 同时管理多本有声书
- 🎧 **TTS 转换** - 使用 Piper 将文本转为语音（完全离线），支持中英文
- ▶️ **音频播放** - 使用 mpv 播放音频，支持流畅的章节切换
- 🔖 **书签功能** - 保存和跳转到任意位置
- ⏸️ **断点续播** - 记住每本书的播放进度
- 🔊 **音量控制** - 实时音量调节，自动保存设置
- ⏩ **播放速度** - 支持 0.5x - 2.0x 播放速度，预设常用档位
- 🎨 **GUI 界面** - 基于 PySide6 的现代化图形界面
- 🚀 **智能缓存** - LRU 缓存机制，优先级调度，快速首次出声
- 🔄 **Chunk 导航** - 精确到 ~100 字的细粒度导航
- 🌐 **XTTS 支持** - 支持 Coqui XTTS 在线合成（可选）
- 💾 **本地存储** - SQLite 数据库，所有数据本地保存
- 📴 **完全离线** - Piper TTS 无需网络连接

## 系统要求

- **操作系统**: Linux（推荐），macOS，或其他 Unix-like 系统
- **Python**: 3.10 或更高版本
- **依赖程序**:
  - `mpv` - 音频播放器（必需）
  - `piper-tts` - 离线 TTS 引擎（可选，通过 pip 安装）

## 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
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
sudo apt install mpv
```

#### Arch Linux

```bash
sudo pacman -S mpv
```

#### macOS

```bash
brew install mpv
```

### 4. 下载 TTS 模型

使用提供的脚本快速下载推荐模型：

```bash
./download_piper_model.sh
```

脚本支持以下模型：
- **英文**: lessac (medium/small), amy (medium)
- **中文**: 花檐/小雅/朝文 (medium/small)

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
3. **Chunk 导航** - 精确到 ~100 字的细粒度导航
4. **智能缓存** - 优先级调度，快速首次出声（0.1-0.3s）
5. **流畅播放** - 后台预合成，自动播放下一章
6. **进度管理** - 自动保存播放位置，支持断点续播
7. **书签** - 在任意位置添加书签
8. **音量控制** - 实时调节播放音量（0% - 100%），设置自动保存
9. **播放速度** - 调节播放速度（0.5x - 2.0x），支持预设档位（0.5x, 1.0x, 1.25x, 1.5x, 2.0x）

### GUI 界面

- **书籍列表** - 查看和管理所有导入的书籍
- **章节列表** - 浏览和跳转到任意章节
- **播放器** - 播放控制、进度显示、文本高亮、音量和速度调节
- **设置** - 配置 TTS 模型、音频参数等

### TTS 选项

- **Piper TTS** (默认) - 完全离线，支持中英文
- **XTTS** (可选) - Coqui XTTS 在线合成，需要配置服务器

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
  "playback_speed": 1.0
}
```

### 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `tts_engine` | TTS 引擎类型 | `piper` |
| `tts_model` | TTS 模型名称 | `lessac-medium` |
| `audio_cache_size` | 缓存 chunk 数量 | `80` |
| `text_chunk_size` | 每个 chunk 字符数 | `100` |
| `prefetch_chunks` | 预取 chunk 数量 | `2` |
| `volume` | 播放音量 (0.0 - 1.0) | `1.0` |
| `playback_speed` | 播放速度 (0.5 - 2.0) | `1.0` |

## 数据存储

- **配置**: `~/.config/novel-reader/config.json`
- **数据库**: `~/.local/share/novel-reader/library.db`
- **音频**: `~/.local/share/novel-reader/audio/`
- **TTS 模型**: `~/.local/share/novel-reader/models/`

## 故障排除

### TTS 转换失败

- 确认 `piper-tts` 已安装: `python -c "import piper_tts"`
- 使用 `./download_piper_model.sh` 下载 TTS 模型
- 检查模型文件是否在 `~/.local/share/novel-reader/models/`
- 查看日志: `~/.cache/novel-reader/logs/`

### 音频播放失败

- 确认 mpv 已正确安装: `mpv --version`
- 检查音频设备是否正常工作
- 尝试使用 `mpv <audio_file>` 直接播放测试

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

详细架构文档请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。

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
- [Coqui XTTS](https://github.com/coqui-ai/TTS) - 在线 TTS（可选）
- [mpv](https://mpv.io/) - 媒体播放器
- [g2pW](https://github.com/Gregorius/pinyin-g2pW) - 中文转拼音
- [sentence-stream](https://github.com/jjlee/sentence-stream) - 句子分割
