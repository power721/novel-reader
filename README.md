# Novel Reader - 本地有声书管理器

一个完全离线的本地有声书管理器，支持文本转语音（TTS）和音频播放。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 特性

- 📚 **多本书管理** - 同时管理多本有声书
- 🎧 **TTS 转换** - 使用 Piper 将文本转为语音（完全离线）
- ▶️ **音频播放** - 使用 mpv 播放音频
- 🔖 **书签功能** - 保存和跳转到任意位置
- ⏸️ **断点续播** - 记住每本书的播放进度
- 🎨 **TUI 界面** - 优雅的终端界面
- 💾 **本地存储** - SQLite 数据库，所有数据本地保存
- 📴 **完全离线** - 无需网络连接

## 系统要求

- **操作系统**: Linux（推荐），或其他 Unix-like 系统
- **Python**: 3.10 或更高版本
- **依赖程序**:
  - `piper` - TTS 引擎
  - `mpv` - 音频播放器

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
# 安装 mpv
sudo apt update
sudo apt install mpv

# 安装 piper（从源码编译或下载预编译版本）
# 访问 https://github.com/rhasspy/piper/releases
# 下载对应架构的 piper 可执行文件，放置到 /usr/local/bin/
sudo wget <piper-release-url> -O /usr/local/bin/piper
sudo chmod +x /usr/local/bin/piper

# 下载 TTS 模型（可选，首次运行时会自动下载）
# 模型放置在 ~/.local/share/piper/voices/
```

#### Arch Linux

```bash
sudo pacman -S mpv
# piper 可从 AUR 安装: paru/yay -S piper
```

#### macOS

```bash
brew install mpv
# piper 需手动安装
```

### 4. 配置

首次运行会自动创建配置文件和数据库：

```bash
python -m novel_reader
```

配置文件位置：`~/.config/novel-reader/config.json`

## 使用方法

### 启动程序

```bash
python -m novel_reader
```

### 快捷键

- `q` / `Ctrl+C` - 退出
- `↑` `↓` - 导航
- `Enter` - 选择/确认
- `Esc` - 返回上级
- `Space` - 播放/暂停
- `s` - 添加书签
- `l` - 书签列表
- `h` - 帮助

### 工作流程

1. **导入书籍** - 支持导入 TXT 格式的文本文件
2. **转换为音频** - 使用 Piper TTS 将章节转换为音频
3. **播放** - 使用 mpv 播放音频
4. **进度管理** - 自动保存播放位置，支持断点续播
5. **书签** - 在任意位置添加书签

## 目录结构

```
novel-reader/
├── novel_reader/           # 主程序包
│   ├── __init__.py
│   ├── main.py            # 程序入口
│   ├── cli.py             # CLI 命令处理
│   ├── ui/                # TUI 界面
│   ├── core/              # 核心逻辑
│   ├── models/            # 数据模型
│   └── utils/             # 工具函数
├── tests/                 # 测试
├── requirements.txt       # Python 依赖
└── README.md              # 本文件
```

## 配置

编辑配置文件 `~/.config/novel-reader/config.json`:

```json
{
  "library_path": "~/Books",
  "tts_model": "en_US-lessac-medium",
  "tts_voice": "en_US-lessac-medium.onnx",
  "audio_quality": "high",
  "auto_convert": true
}
```

## 数据存储

- **配置**: `~/.config/novel-reader/config.json`
- **数据库**: `~/.local/share/novel-reader/library.db`
- **音频**: `~/.local/share/novel-reader/audio/`
- **TTS 模型**: `~/.local/share/novel-reader/models/`

## 故障排除

### TTS 转换失败

- 确认 piper 已正确安装: `piper --help`
- 检查 TTS 模型是否下载完成
- 查看日志: `~/.cache/novel-reader/logs/`

### 音频播放失败

- 确认 mpv 已正确安装: `mpv --version`
- 检查音频文件是否存在
- 确认系统音频输出正常

### 中文支持

如需中文 TTS，下载中文模型：

```bash
wget https://huggingface.co/rhasspy/piper-voices/v1/models/zh_CN-huayan-medium.tar.gz
tar xzf zh_CN-huayan-medium.tar.gz
mv zh_CN-huayan-medium ~/.local/share/novel-reader/models/
```

## 开发

```bash
# 运行测试
python -m pytest tests/

# 代码格式化
black novel_reader/
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [Textual](https://github.com/Textualize/textual) - TUI 框架
- [Piper](https://github.com/rhasspy/piper) - 快速离线 TTS
- [mpv](https://mpv.io/) - 媒体播放器
