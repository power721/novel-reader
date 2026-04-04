#!/bin/bash
# Local build script for testing packaging

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Novel Reader - 本地打包测试${NC}"
echo -e "${GREEN}========================================${NC}"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=macos;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM=windows;;
    *)          PLATFORM="unknown:${OS}"
esac

echo -e "${YELLOW}检测到平台: $PLATFORM${NC}"

# Build with PyInstaller
echo -e "\n${YELLOW}[1/3] 使用 PyInstaller 构建...${NC}"
pyinstaller novel_reader.spec --clean --noconfirm

# Platform-specific packaging
echo -e "\n${YELLOW}[2/3] 平台特定打包...${NC}"
case "${PLATFORM}" in
    linux)
        if [ -f "scripts/build_appimage.sh" ]; then
            bash scripts/build_appimage.sh
        else
            echo -e "${YELLOW}跳过 AppImage 构建 (脚本不存在)${NC}"
        fi
        ;;
    macos)
        if [ -f "scripts/build_macos.sh" ]; then
            bash scripts/build_macos.sh
        else
            echo -e "${YELLOW}跳过 macOS 打包 (脚本不存在)${NC}"
        fi
        ;;
    windows)
        if [ -f "scripts/build_windows.py" ]; then
            python scripts/build_windows.py
        else
            echo -e "${YELLOW}跳过 Windows 打包 (脚本不存在)${NC}"
        fi
        ;;
esac

# Summary
echo -e "\n${YELLOW}[3/3] 构建完成${NC}"
echo -e "${GREEN}构建产物:${NC}"
ls -lh dist/ | grep -E '\.(AppImage|exe|zip|tar\.gz)$' || echo "未找到打包文件"

echo -e "\n${GREEN}测试运行:${NC}"
case "${PLATFORM}" in
    linux)
        echo "  ./dist/novel-reader/novel-reader"
        ;;
    macos)
        echo "  open dist/novel-reader.app"
        ;;
    windows)
        echo "  dist\\novel-reader\\novel-reader.exe"
        ;;
esac
