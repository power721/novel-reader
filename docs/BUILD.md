# Novel Reader 打包指南

本文档说明如何将 Novel Reader 打包为 Linux 可执行程序。

## 前置要求

### 1. 系统依赖

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv mpv
```

### 2. Python 依赖

确保已安装所有必需的 Python 包：

```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 打包步骤

### 快速打包

使用提供的打包脚本：

```bash
./build.sh
```

该脚本会自动：
1. 检查系统依赖
2. 清理旧的构建文件
3. 使用 PyInstaller 打包
4. 创建发布包
5. 生成压缩包

### 手动打包

如果需要更多控制，可以手动运行：

```bash
# 1. 清理旧的构建
./clean_build.sh

# 2. 使用 PyInstaller 打包
pyinstaller novel_reader.spec

# 3. 运行生成的可执行文件
./dist/novel-reader
```

## 输出文件

打包完成后，会在 `dist/` 目录下生成：

```
dist/
├── novel-reader                      # 可执行文件
└── novel-reader-linux/               # 发布目录
    ├── novel-reader                  # 可执行文件
    ├── g2pW/                         # 数据文件
    ├── models/                       # TTS 模型目录
    ├── audio/                        # 音频缓存目录
    ├── start.sh                      # 启动脚本
    ├── README.txt                    # 用户说明
    └── INSTALL.md                    # 安装指南
```

以及压缩包：

```
dist/novel-reader-YYYYMMDD-linux-x86_64.tar.gz
```

## 分发

### 1. 测试打包结果

在打包机器上测试：

```bash
cd dist/novel-reader-linux
./start.sh
```

### 2. 分发给用户

将压缩包发送给用户：

```bash
# 用户解压
tar -xzf novel-reader-YYYYMMDD-linux-x86_64.tar.gz
cd novel-reader-linux

# 用户安装系统依赖
sudo apt install mpv

# 用户运行
./start.sh
```

## 系统要求

打包后的程序在目标系统上需要：

### 必需依赖

- **mpv 播放器**: 用于音频播放
  ```bash
  sudo apt install mpv
  ```

### 可选依赖

- **piper-tts 模型**: 用于离线 TTS
  - 需要下载到 `~/.local/share/novel-reader/models/`
  - 使用 `download_piper_model.sh` 下载

## 配置文件

程序首次运行会在用户目录创建：

- **配置**: `~/.config/novel-reader/config.json`
- **数据库**: `~/.local/share/novel-reader/library.db`
- **音频缓存**: `~/.local/share/novel-reader/audio/`
- **日志**: `~/.cache/novel-reader/logs/`

## 故障排除

### 打包失败

1. **PyInstaller 版本问题**
   ```bash
   pip install --upgrade pyinstaller
   ```

2. **缺少依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **隐藏导入缺失**
   编辑 `novel_reader.spec` 文件，添加到 `hiddenimports` 列表

### 运行时错误

1. **找不到 mpv**
   - 确保目标系统已安装 mpv
   - 使用 `which mpv` 检查

2. **TTS 无法工作**
   - 检查模型文件是否存在
   - 查看日志文件了解详细错误

3. **权限问题**
   ```bash
   chmod +x novel-reader
   ```

## 高级配置

### 修改打包配置

编辑 `novel_reader.spec` 文件：

```python
# 添加更多隐藏导入
hiddenimports = [
    'your_module',
]

# 添加数据文件
datas = [
    ('path/to/data', 'destination'),
]
```

### 优化体积

1. **排除不需要的模块**:
   ```python
   excludes=[
       'matplotlib',
       'numpy',
       # ... 其他不需要的模块
   ]
   ```

2. **使用 UPX 压缩** (已默认启用)

3. **单文件模式** (不推荐，启动较慢):
   ```python
   exe = EXE(
       # ... 其他参数
       exclude_binaries=False,  # 改为 False
       onefile=True,  # 添加这个参数
   )
   ```

### 添加应用图标

准备一个 `.png` 图标文件，转换为 `.ico`：

```bash
# 安装工具
sudo apt install imagemagick

# 转换图标
convert icon.png -define icon:auto-resize=256,128,96,64,48,32,16 icon.ico
```

然后在 `novel_reader.spec` 中指定：

```python
exe = EXE(
    # ... 其他参数
    icon='icon.ico',
)
```

## CI/CD 集成

可以在 CI/CD 流水线中自动打包：

```yaml
# .github/workflows/build.yml 示例
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: |
          sudo apt install mpv
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build
        run: ./build.sh

      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: novel-reader-linux
          path: dist/novel-reader-*.tar.gz
```

## 相关文档

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [项目 README](../README.md)
- [架构文档](../ARCHITECTURE.md)
