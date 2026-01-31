#!/bin/bash
# Piper TTS 模型下载脚本
# 用于快速下载推荐的语音模型

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Piper TTS 模型下载脚本${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# 创建模型目录
mkdir -p models
cd models

echo "请选择要下载的模型:"
echo ""
echo -e "${BLUE}=== 英文模型 ===${NC}"
echo "1) 英文 lessac - medium (推荐，~80MB)"
echo "2) 英文 lessac - small (轻量，~30MB)"
echo ""
echo -e "${BLUE}=== 中文模型 ===${NC}"
echo "3) 中文 花檐 - medium (推荐，~80MB)"
echo "4) 中文 花檐 - small (轻量，~30MB)"
echo "5) 中文 小雅 - medium (女声，~80MB)"
echo "6) 中文 朝文 - medium (~80MB)"
echo ""
echo -e "${BLUE}=== 批量下载 ===${NC}"
echo "7) 下载全部英文模型"
echo "8) 下载全部中文模型"
echo "9) 下载全部模型"
echo ""
read -p "请输入选项 (1-9): " choice

case $choice in
    1)
        echo -e "${YELLOW}下载英文 lessac medium 模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
        ;;
    2)
        echo -e "${YELLOW}下载英文 lessac small 模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx.json
        ;;
    3)
        echo -e "${YELLOW}下载中文 花檐 medium 模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
        ;;
    4)
        echo -e "${YELLOW}下载中文 花檐 small 模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx.json
        ;;
    5)
        echo -e "${YELLOW}下载中文 小雅 medium 模型（女声）...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json
        ;;
    6)
        echo -e "${YELLOW}下载中文 朝文 medium 模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json
        ;;
    7)
        echo -e "${YELLOW}下载全部英文模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx.json
        ;;
    8)
        echo -e "${YELLOW}下载全部中文模型...${NC}"
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json
        ;;
    9)
        echo -e "${YELLOW}下载全部模型...${NC}"
        # 英文模型
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/small/en_US-lessac-small.onnx.json
        # 中文模型
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/zh/zh_CN/huayan/small/zh_CN-huayan-small.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx
        wget -c https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium.onnx.json
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

cd ..

echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}下载完成！${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "模型文件已下载到 models/ 目录"
echo ""
echo "已下载的模型:"
ls -lh models/*.onnx 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "下一步:"
echo "1. 运行测试: python test_piper.py"
echo "2. 启动 GUI: python -m novel_reader"
echo ""
