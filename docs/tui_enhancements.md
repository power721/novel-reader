# TUI 交互增强功能说明

## 新增功能

### 1. 章节播放
在章节列表中按 `Enter`，从该章节的起始 chunk 开始播放。

### 2. 书签播放
在书签列表中按 `Enter`，从书签位置开始播放。

### 3. 添加书签
按 `b` 键，在当前播放进度位置添加书签。

## 快捷键对照表

| 按键 | 功能 | 适用位置 |
|------|------|----------|
| `Enter` | 播放选中项 | 所有列表 |
| `Enter` | 播放书籍（从断点） | 书籍列表 |
| `Enter` | 播放章节（从起始位置） | 章节列表 |
| `Enter` | 播放书签位置 | 书签列表 |
| `b` | 添加书签到当前进度 | 任意位置 |
| `q` | 退出程序 | 任意位置 |
| `←` `→` `↑` `↓` | 导航 | 任意位置 |
| `h` `j` `k` `l` | Vim 风格导航 | 任意位置 |

## 使用场景

### 场景 1: 从章节开始播放
1. 在书籍列表选择一本书
2. 按 `→` 移动到章节列表
3. 用方向键选择章节
4. 按 `Enter` 开始播放

### 场景 2: 从书签继续
1. 在书籍列表选择一本书
2. 按 `→` 两次移动到书签列表
3. 用方向键选择书签
4. 按 `Enter` 跳转到书签位置播放

### 场景 3: 添加书签
1. 在书籍列表选择一本书
2. 按 `b` 添加书签到当前播放进度
3. 书签列表自动刷新

## 代码结构

### 新增文件
- `novel_reader/core/bookmark.py` - 书签管理模块

### 修改文件
- `novel_reader/ui/tui.py` - 增强交互逻辑

### 导出函数
```python
from novel_reader.core import add_bookmark, get_bookmarks, delete_bookmark, update_bookmark
```

## 实现细节

### 智能播放识别
TUI 自动识别当前聚焦的表格：
- 书籍表 → 从 current_chunk 播放
- 章节表 → 从章节的 start_chunk 播放
- 书签表 → 从书签的 chunk 播放

### 书签数据结构
```python
{
    "id": 1,
    "book_id": 1,
    "chunk": 10,
    "note": "Chunk 10",
    "created_at": "2026-01-31 12:00:00"
}
```

## 测试

```bash
# 测试书签模块
python -m novel_reader.core.bookmark

# 启动 TUI 测试
python -m novel_reader
```
