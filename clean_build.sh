#!/bin/bash
# 清理构建产物

echo "清理 PyInstaller 构建文件..."

rm -rf build/
rm -rf dist/
rm -rf *.spec.build

echo "✓ 清理完成"
