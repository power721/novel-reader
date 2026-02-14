#!/bin/bash
# Novel Reader - Linux 可执行程序打包脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Novel Reader - 打包脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检测 Python 环境
if [ -d ".venv" ]; then
    echo -e "${YELLOW}检测到项目虚拟环境 .venv${NC}"
    export PATH=".venv/bin:$PATH"
    PYTHON_CMD=".venv/bin/python"
    PIP_CMD=".venv/bin/pip"
elif [ -d "venv" ]; then
    echo -e "${YELLOW}检测到项目虚拟环境 venv${NC}"
    export PATH="venv/bin:$PATH"
    PYTHON_CMD="venv/bin/python"
    PIP_CMD="venv/bin/pip"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    echo -e "${YELLOW}使用系统 Python 环境${NC}"
fi

# 检查依赖
echo -e "\n${YELLOW}[1/6] 检查系统依赖...${NC}"

# 检查 PyInstaller
if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    echo -e "${RED}未安装 PyInstaller，正在安装...${NC}"
    $PIP_CMD install pyinstaller
fi

# 检查 mpv
if ! command -v mpv &> /dev/null; then
    echo -e "${RED}警告: 未检测到 mpv 播放器${NC}"
    echo -e "${YELLOW}请安装 mpv: sudo apt install mpv${NC}"
    echo -e "${YELLOW}打包的程序仍需要系统安装 mpv 才能正常工作${NC}"
fi

# 检查 piper-tts
echo -e "${YELLOW}检查 piper-tts 安装...${NC}"
if ! $PYTHON_CMD -c "import piper_tts" 2>/dev/null; then
    echo -e "${RED}警告: piper-tts 未正确安装${NC}"
    echo -e "${YELLOW}请运行: $PIP_CMD install piper-tts>=1.2.0${NC}"
fi

# 清理旧的构建
echo -e "\n${YELLOW}[2/6] 清理旧的构建文件...${NC}"
rm -rf build/ dist/

# 创建临时目录
mkdir -p dist/

# 使用 PyInstaller 打包
echo -e "\n${YELLOW}[3/6] 使用 PyInstaller 打包...${NC}"
$PYTHON_CMD -m PyInstaller novel_reader.spec \
    --clean \
    --noconfirm

# 检查构建结果
# PyInstaller 的 COLLECT 会创建 dist/novel-reader/ 目录
if [ ! -d "dist/novel-reader" ]; then
    echo -e "${RED}打包失败！${NC}"
    exit 1
fi

# 检查可执行文件
if [ ! -f "dist/novel-reader/novel-reader" ]; then
    echo -e "${RED}可执行文件生成失败！${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 可执行文件生成成功${NC}"

# 创建发布包
echo -e "\n${YELLOW}[4/6] 创建发布包...${NC}"

RELEASE_DIR="dist/novel-reader-linux"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# 复制整个 PyInstaller 输出目录
cp -r dist/novel-reader/* "$RELEASE_DIR/"

# 复制 g2pW 数据文件
if [ -d "g2pW" ]; then
    cp -r g2pW "$RELEASE_DIR/"
fi

# 创建必要的目录结构
mkdir -p "$RELEASE_DIR/models"
mkdir -p "$RELEASE_DIR/audio"

# 创建 README
cat > "$RELEASE_DIR/README.txt" << 'EOF'
Novel Reader - 本地有声书管理器
================================

运行方式:
    ./novel-reader              # 启动 GUI

系统要求:
    - Linux x86_64
    - mpv 播放器 (必需): sudo apt install mpv
    - Python 3.11+ (仅用于开发，运行时不需要)

数据目录:
    - 配置: ~/.config/novel-reader/
    - 数据库: ~/.local/share/novel-reader/library.db
    - 音频缓存: ~/.local/share/novel-reader/audio/
    - TTS 模型: ~/.local/share/novel-reader/models/

TTS 模型下载:
    首次运行前，请下载 TTS 模型：
    bash download_piper_model.sh

或者手动下载:
    https://huggingface.co/rhasspy/piper-voices

项目主页:
    https://github.com/yourusername/novel-reader

问题反馈:
    请在 GitHub Issues 中报告问题
EOF

# 创建启动脚本
cat > "$RELEASE_DIR/start.sh" << 'EOF'
#!/bin/bash
# Novel Reader 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$SCRIPT_DIR:$PATH"

# 检查 mpv
if ! command -v mpv &> /dev/null; then
    echo "错误: 未检测到 mpv 播放器"
    echo "请安装: sudo apt install mpv"
    exit 1
fi

# 启动程序
exec "$SCRIPT_DIR/novel-reader" "$@"
EOF

chmod +x "$RELEASE_DIR/start.sh"

# 创建安装说明
cat > "$RELEASE_DIR/INSTALL.md" << 'EOF'
# Novel Reader 安装说明

## 快速开始

1. **安装系统依赖**
   ```bash
   sudo apt update
   sudo apt install mpv
   ```

2. **运行程序**
   ```bash
   ./start.sh
   # 或直接运行
   ./novel-reader
   ```

3. **下载 TTS 模型**（首次使用）

   使用提供的脚本下载：
   ```bash
   bash download_piper_model.sh
   ```

   或手动下载并放置到 `~/.local/share/novel-reader/models/`

## 可选：安装到系统

创建符号链接到系统路径：
```bash
sudo ln -s "$(pwd)/novel-reader" /usr/local/bin/novel-reader
```

## 故障排除

### 程序无法启动
- 检查是否安装了 mpv: `which mpv`
- 查看日志: `~/.cache/novel-reader/logs/`

### TTS 无法工作
- 确认模型已下载到正确位置
- 检查磁盘空间是否充足

### 权限问题
- 确保程序有执行权限: `chmod +x novel-reader`
EOF

# 创建压缩包
echo -e "\n${YELLOW}[5/6] 创建压缩包...${NC}"
cd dist
tar -czf "novel-reader-$(date +%Y%m%d)-linux-x86_64.tar.gz" "novel-reader-linux"
cd ..

# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  打包完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}可执行文件: ${NC}dist/novel-reader"
echo -e "${GREEN}发布目录: ${NC}$RELEASE_DIR"
echo -e "${GREEN}压缩包: ${NC}dist/novel-reader-$(date +%Y%m%d)-linux-x86_64.tar.gz"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo "1. 请确保目标系统安装了 mpv 播放器"
echo "2. TTS 模型需要单独下载到 ~/.local/share/novel-reader/models/"
echo "3. 首次运行会自动创建必要的配置和数据目录"
echo ""
echo -e "${GREEN}测试运行: ${NC}cd $RELEASE_DIR && ./start.sh"
echo ""
echo -e "${YELLOW}Python 环境信息:${NC}"
echo "使用: $PYTHON_CMD"
echo ""
