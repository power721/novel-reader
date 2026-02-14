# 解决 PyInstaller conda 环境兼容性问题

## 问题

如果在 Miniforge3/Anaconda 环境中遇到 PyInstaller 错误：

```
KeyError: 'depends'
```

## 解决方案

### 方案 1：使用项目虚拟环境（推荐）

项目已经有一个 `.venv` 虚拟环境，构建脚本会自动检测并使用：

```bash
./build.sh
```

如果 `.venv` 不存在，创建一个：

```bash
# 使用 venv（标准方式）
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

# 现在可以运行构建脚本
./build.sh
```

### 方案 2：在 conda 环境中修复

如果想继续使用 conda 环境：

```bash
# 升级 PyInstaller 到最新版本
pip install --upgrade pyinstaller

# 或者降级 conda 的元数据格式
conda update --all
```

### 方案 3：临时切换到系统 Python

```bash
# 直接指定使用系统 Python
PYTHON_CMD=python3 ./build.sh

# 或者
python3 -m PyInstaller novel_reader.spec
```

## 验证环境

运行以下命令检查当前使用的 Python：

```bash
# 检查 Python 路径
which python

# 检查是否在 conda 环境中
echo $CONDA_PREFIX

# 检查虚拟环境
echo $VIRTUAL_ENV
```

## 推荐的打包流程

```bash
# 1. 确保使用干净的虚拟环境
source .venv/bin/activate  # 或激活 .venv

# 2. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 3. 运行打包脚本
./build.sh

# 4. 测试打包结果
./test_build.sh
```

## 常见问题

### Q: 为什么要使用 venv 而不是 conda？

A: PyInstaller 在某些 conda 环境中存在已知兼容性问题，特别是与包元数据格式相关。使用标准的 Python venv 环境可以避免这些问题。

### Q: 可以继续使用 conda 进行开发吗？

A: 可以！只需要在打包时切换到 venv 环境，或者使用方案 3 临时指定系统 Python。

### Q: 打包后的程序可以在 conda 环境中运行吗？

A: 可以。打包后的程序是独立的可执行文件，不需要任何 Python 环境。

## 相关文件

- `build.sh` - 主打包脚本（自动检测并使用 .venv）
- `novel_reader.spec` - PyInstaller 配置文件
- `docs/BUILD.md` - 详细打包文档
