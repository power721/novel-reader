#!/bin/bash
# Create and push a new release tag

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}用法: $0 <版本号>${NC}"
    echo -e "${YELLOW}示例: $0 v1.0.0${NC}"
    exit 1
fi

VERSION="$1"

# Validate version format
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}错误: 版本号格式不正确${NC}"
    echo -e "${YELLOW}格式应为: vX.Y.Z (例如: v1.0.0)${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  创建发布标签: $VERSION${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo -e "${RED}错误: 标签 $VERSION 已存在${NC}"
    echo -e "${YELLOW}如需删除现有标签，运行:${NC}"
    echo "  git tag -d $VERSION"
    echo "  git push origin :refs/tags/$VERSION"
    exit 1
fi

# Check working tree status
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}错误: 工作目录有未提交的更改${NC}"
    echo -e "${YELLOW}请先提交或暂存所有更改${NC}"
    git status
    exit 1
fi

# Show current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${YELLOW}当前分支: $BRANCH${NC}"

# Confirm
echo -e "\n${YELLOW}即将创建并推送标签: $VERSION${NC}"
read -p "确认? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消"
    exit 0
fi

# Create tag
echo -e "\n${YELLOW}创建标签...${NC}"
git tag -a "$VERSION" -m "Release $VERSION"

# Show tag info
echo -e "\n${YELLOW}标签信息:${NC}"
git show "$VERSION" --quiet

# Push tag
echo -e "\n${YELLOW}推送标签到 GitHub...${NC}"
git push origin "$VERSION"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  标签已创建并推送${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions 将自动构建并发布${NC}"
echo -e "${YELLOW}查看构建进度:${NC}"
echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo -e "${YELLOW}构建完成后，发布包将出现在:${NC}"
echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/tag/$VERSION"
echo ""
