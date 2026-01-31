# 更改书名功能

## 功能概述

添加了书籍重命名功能，允许用户在GUI中方便地修改书名。

## 实现细节

### 1. 核心功能 (`novel_reader/core/book.py`)

新增函数 `update_book_title()`:

```python
def update_book_title(book_id: int, new_title: str) -> bool:
    """
    更新书籍标题

    Args:
        book_id: 书籍 ID
        new_title: 新书名

    Returns:
        是否更新成功
    """
```

**特性:**
- 验证书名非空
- 自动trim首尾空格
- 更新updated_at时间戳
- 返回操作结果

### 2. GUI对话框 (`novel_reader/gui/dialogs/rename_book_dialog.py`)

创建了 `RenameBookDialog` 对话框:

**功能:**
- 显示当前书名
- 输入新书名（自动选中全部文本）
- 验证输入
- 确认/取消按钮

**辅助函数:**
```python
def rename_book_dialog(parent, current_title: str) -> str:
    """
    显示重命名对话框

    Returns:
        新书名，如果取消则返回空字符串
    """
```

### 3. BookListWidget更新 (`novel_reader/gui/widgets/book_list_widget.py`)

**新增信号:**
```python
book_rename_requested = Signal(int, str)  # (book_id, current_title)
```

**右键菜单新增:**
- ✏️ 重命名
- 🗑️ 删除书籍

### 4. MainWindow集成

**旧版MainWindow (`main_window.py`):**
- 添加 `_on_rename_book()` 槽函数
- 连接信号到槽
- 更新后刷新列表和状态栏

**新版MainWindow V2 (`main_window_v2.py`):**
- 同样的实现
- 与新架构兼容

## 使用方法

### 方法1: 右键菜单重命名

1. 在书籍列表中找到要重命名的书籍
2. **右键点击**书籍
3. 选择 **"✏️ 重命名"**
4. 在弹出的对话框中输入新的书名
5. 点击 **"确定"**

### 方法2: 编程调用

```python
from novel_reader.core import update_book_title

# 更新书名
success = update_book_title(book_id=1, new_title="新书名")

if success:
    print("重命名成功")
else:
    print("重命名失败")
```

## 测试

### 运行测试套件

```bash
python novel_examples/test_rename_book.py
```

### 测试覆盖

✅ **核心函数测试**
- 基本更新功能
- 空书名拒绝
- 空格trim
- 时间戳更新

✅ **对话框测试**
- 对话框创建
- 输入验证
- 返回值正确性

✅ **GUI集成测试**
- 信号定义
- 右键菜单
- 主窗口槽函数

## 测试结果

```
✅ 所有测试通过!

📝 使用方法:
  1. 在书籍列表中右键点击书籍
  2. 选择 '✏️ 重命名'
  3. 输入新的书名
  4. 点击确定
```

## 数据库变更

**无需迁移** - 使用现有字段:

```sql
UPDATE book
SET title = ?, updated_at = ?
WHERE id = ?
```

## 用户界面

### 右键菜单

```
┌─────────────────┐
│ ✏️ 重命名       │
│ 🗑️ 删除书籍     │
└─────────────────┘
```

### 重命名对话框

```
┌─────────────────────────────┐
│        重命名书籍            │
├─────────────────────────────┤
│ 请输入新的书名:              │
│                             │
│ 当前书名: 原始书名           │
│                             │
│ [新的书名输入框             │
│                             │
│        [取消]  [确定]       │
└─────────────────────────────┘
```

## 验证规则

1. **非空验证**: 书名不能为空
2. **空格处理**: 自动trim首尾空格
3. **重复检查**: 允许相同书名（不同书籍）
4. **变更检测**: 如果书名未改变，提示用户

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 空书名 | 拒绝，提示"书名不能为空" |
| 纯空格 | 拒绝，提示"书名不能为空" |
| 书名未改变 | 提示"书名未改变"，关闭对话框 |
| 数据库错误 | 返回False，打印错误日志 |
| 书籍不存在 | 返回False，打印错误日志 |

## 文件清单

### 新增文件
- `novel_reader/gui/dialogs/rename_book_dialog.py` - 重命名对话框
- `novel_examples/test_rename_book.py` - 功能测试套件

### 修改文件
- `novel_reader/core/book.py` - 添加update_book_title()函数
- `novel_reader/core/__init__.py` - 导出新函数
- `novel_reader/gui/widgets/book_list_widget.py` - 添加重命名信号和菜单项
- `novel_reader/gui/dialogs/__init__.py` - 导出对话框
- `novel_reader/gui/main_window.py` - 添加重命名处理
- `novel_reader/gui/main_window_v2.py` - 添加重命名处理

## 后续增强

可选的功能改进:

1. **批量重命名**: 支持批量重命名书籍
2. **重命名历史**: 记录书名变更历史
3. **自动命名**: 根据文件内容智能命名
4. **快捷键**: 添加F2快捷键重命名
5. **撤销功能**: 支持撤销重命名操作

## 兼容性

- ✅ 旧版MainWindow (PlaybackWorker架构)
- ✅ 新版MainWindow V2 (PlaybackController架构)
- ✅ 命令行工具
- ✅ 现有数据库（无需迁移）
