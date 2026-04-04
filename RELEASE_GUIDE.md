# 快速发布指南

本文档提供快速发布新版本的步骤。

## 一键发布

```bash
# 1. 更新 CHANGELOG.md
vim CHANGELOG.md

# 2. 提交更改
git add CHANGELOG.md
git commit -m "Prepare for release v1.0.0"
git push

# 3. 创建标签并自动发布
bash scripts/release.sh v1.0.0
```

## 发布流程说明

1. **更新 CHANGELOG** - 记录本版本的更改
2. **推送标签** - 触发 GitHub Actions 自动构建
3. **等待构建** - 约 15-30 分钟完成所有平台构建
4. **验证发布** - 在 GitHub Releases 页面检查构建产物

## 监控构建

推送标签后，访问 Actions 页面查看构建进度：
```
https://github.com/<your-username>/novel-reader/actions
```

## 下载构建产物

构建完成后，在 Releases 页面下载：
```
https://github.com/<your-username>/novel-reader/releases
```

## 版本号规范

- `v1.0.0` - 首个稳定版本
- `v1.0.1` - Bug 修复
- `v1.1.0` - 新功能
- `v2.0.0` - 重大更新

## 故障排除

### 构建失败

查看 GitHub Actions 日志，修复问题后：
```bash
# 删除失败标签
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# 修复后重新发布
bash scripts/release.sh v1.0.0
```

### 本地测试

发布前先本地测试：
```bash
bash scripts/build_all.sh
```

## 相关文档

- [详细打包指南](docs/PACKAGING.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)
- [打包总结](docs/PACKAGING_SUMMARY.md)
