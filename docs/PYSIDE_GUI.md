# Novel Reader - PySide6 GUI 使用说明

## 项目概述

完整的本地有声书管理器 GUI，使用 PySide6 实现。

### 特性

- ✅ **模块化设计**：清晰的组件分离，易于维护和扩展
- ✅ **拖拽导入**：支持将 `.txt` 文件拖入窗口直接导入
- ✅ **三栏布局**：书籍列表、章节列表、书签列表
- ✅ **播放控制**：播放/停止，进度显示
- ✅ **TTS 转换**：后台转换，进度条和日志显示
- ✅ **书签管理**：添加/删除书签，支持笔记
- ✅ **双击播放**：双击书籍/章节/书签直接播放

## 项目结构

```
novel_reader/
├── core/              # 核心业务逻辑
├── models/            # 数据库层
├── utils/             # 工具函数
├── gui/               # PySide6 GUI
│   ├── widgets/       # 自定义组件
│   ├── workers/       # 后台工作线程
│   ├── dialogs/       # 对话框
│   ├── main_window.py # 主窗口
│   └── pyside_main.py # GUI 入口
└── __main__.py        # 程序入口
```

## 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `PySide6>=6.6.0` - Qt for Python

## 运行方式

### 方式一：使用模块运行（推荐）

```bash
# 运行 GUI
python -m novel_reader

# 运行 GUI 并创建测试数据
python -m novel_reader --test

# 运行 TUI 界面
python -m novel_reader --tui
```

### 方式二：直接运行 GUI 模块

```bash
# 运行 GUI
python -m novel_reader.gui.pyside_main

# 运行 GUI 并创建测试数据
python -m novel_reader.gui.pyside_main --test
```

### 方式三：作为包导入

```python
from novel_reader.gui import run_gui

run_gui(create_test=False)
```

## 功能说明

### 1. 导入书籍

- **拖拽导入**：直接将 `.txt` 文件拖到窗口中
- **菜单导入**：文件 → 导入书籍

### 2. 播放音频

- 选择书籍后点击「▶ 播放」按钮
- 双击书籍/章节/书签快速播放
- 播放进度自动保存到数据库

### 3. TTS 转换

- 选择书籍后点击「转换整本书」
- 查看实时转换日志
- 已转换的 chunk 会自动跳过

### 4. 书签管理

- 点击「添加书签」在当前位置添加书签
- 点击「添加笔记」添加带笔记的书签
- 双击书签跳转到对应位置

### 5. 快捷键

- `Ctrl+I` - 导入书籍
- `F5` - 刷新列表
- `Ctrl+Q` - 退出程序

## 代码架构

### 组件（widgets）

| 组件 | 文件 | 功能 |
|------|------|------|
| BookListWidget | `book_list_widget.py` | 书籍列表，支持拖拽 |
| ChapterListWidget | `chapter_list_widget.py` | 章节列表 |
| BookmarkListWidget | `bookmark_list_widget.py` | 书签列表 |
| PlayerWidget | `player_widget.py` | 播放控制 |
| TTSWidget | `tts_widget.py` | TTS 转换 |

### 工作线程（workers）

| 线程 | 文件 | 功能 |
|------|------|------|
| PlaybackWorker | `playback_worker.py` | 后台播放 |
| TTSWorker | `tts_worker.py` | TTS 转换 |

### 对话框（dialogs）

| 对话框 | 文件 | 功能 |
|--------|------|------|
| AboutDialog | `about_dialog.py` | 关于信息 |

## 扩展开发

### 添加新的 Widget

1. 在 `gui/widgets/` 创建新文件
2. 继承 `QWidget`
3. 定义信号（Signal）
4. 在 `widgets/__init__.py` 导出

### 添加新的 Worker

1. 在 `gui/workers/` 创建新文件
2. 继承 `QThread`
3. 定义信号（Signal）
4. 实现运行逻辑
5. 在 `workers/__init__.py` 导出

## 技术细节

### 信号与槽机制

```python
# 定义信号
book_selected = Signal(int)  # 参数：book_id

# 连接信号
self.book_list_widget.book_selected.connect(self._on_book_selected)

# 发送信号
self.book_selected.emit(book_id)
```

### 后台工作线程

```python
class Worker(QThread):
    finished = Signal()
    error = Signal(str)

    def run(self):
        # 后台任务
        try:
            do_work()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()
```

## 已知问题

- RuntimeWarning: 模块导入警告（不影响功能）
- AtSpiAdaptor 警告（可忽略，辅助功能相关）

## 许可证

MIT License
