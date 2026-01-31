# 章节点击自动转换功能测试指南

## 修复内容

### 问题
启动程序后点击章节没有自动转换，而是报错：
```
错误: 没有可用的音频文件
请先进行 TTS 转换！
```

### 根本原因
程序启动后没有自动选中书籍，导致 `current_book_id` 为 None。

### 修复方案
1. **自动选中第一本书** - 程序启动时自动选中第一本书
2. **增强调试信息** - 添加详细的调试日志
3. **统一事件处理** - 单击和双击章节都使用相同的逻辑

## 测试步骤

### 1. 启动程序

```bash
python -m novel_reader --test
```

**预期输出**：
```
Database initialized at: /home/harold/workspace/novel-reader/data/library.db
正在创建测试数据...
✓ 导入成功: novel_reader_test
  书籍 ID: 5
  总段数: 13
  章节数: 120
✓ 测试数据创建成功
[INFO] Auto-selected book: 5 - novel_reader_test
```

### 2. 检查界面状态

**左侧 - 书籍列表**：
- ✓ 应该自动选中第一本书（高亮显示）
- ✓ 右侧应该显示章节列表
- ✓ 右侧应该显示书签列表

### 3. 点击章节

**单击任意章节**：
- 查看控制台输出，应该看到：
  ```
  [DEBUG] _on_chapter_selected called: start_chunk=XX, current_book_id=5
  [DEBUG] Found X chapters
  [DEBUG] Chapter range: XX - XX
  [DEBUG] Chapter has audio: False
  [DEBUG] Calling _convert_chapter_and_play
  ```

- TTS 日志区域应该显示：
  ```
  开始转换当前章节 (chunk XX - XX)
  [XX/749] 正在转换...
  [XX/749] 转换完成
  ...
  ✓ 当前章节转换完成！开始播放...
  ```

### 4. 查看播放状态

- 状态栏显示：`正在播放 from chunk: XX`
- 播放控制按钮：▶ 变为不可用，⏹ 变为可用
- 进度条显示播放进度

## 故障排查

### 如果点击章节没有反应

**检查 1** - 查看控制台输出
```bash
# 应该看到调试信息
[DEBUG] _on_chapter_selected called: start_chunk=XX, current_book_id=5
```

如果看到 `current_book_id=None`，说明书籍没有选中。

**检查 2** - 手动点击书籍
1. 在左侧书籍列表中点击任意一本书
2. 查看状态栏是否显示 `已选择书籍 ID: X`
3. 然后再点击章节

**检查 3** - 查看章节列表
- 右侧章节列表应该显示章节
- 如果显示"暂无章节"，说明章节解析失败

### 如果 TTS 转换失败

**检查模型文件**：
```bash
ls -lh models/
```

应该看到模型文件：
```
zh_CN-huayan-medium.onnx
zh_CN-huayan-medium.onnx.json
```

**检查 TTS 日志**：
- 在 GUI 下方查看 TTS 日志区域
- 应该看到转换进度和错误信息

## 调试模式

### 启用详细调试

在 `main_window.py` 中，所有关键方法都有调试输出：

```python
[DEBUG] _on_chapter_selected called: start_chunk=XX, current_book_id=5
[DEBUG] Found X chapters
[DEBUG] Chapter range: XX - XX
[DEBUG] Chapter has audio: False
[DEBUG] Calling _convert_chapter_and_play
```

### 如果问题依然存在

请提供以下信息：

1. **控制台输出** - 完整的启动和点击章节的输出
2. **操作步骤** - 具体做了什么操作
3. **界面状态** - 各个列表显示的内容
4. **错误信息** - 完整的错误消息

## 代码变更摘要

### 文件：`novel_reader/gui/widgets/book_list_widget.py`

**变更**：加载书籍后自动选中第一本书

```python
# 自动选中第一本书（如果没有选中任何书籍）
if books and not self.books_tree.selectedItems():
    first_item = self.books_tree.topLevelItem(0)
    self.books_tree.setCurrentItem(first_item)
    book_id = int(first_item.text(0))
    self.current_book_id = book_id
    self.book_selected.emit(book_id)
```

### 文件：`novel_reader/gui/main_window.py`

**变更**：
1. 添加详细的调试信息
2. `_on_chapter_selected` - 检查章节音频状态
3. `_on_chapter_double_clicked` - 使用相同的逻辑
4. `_convert_chapter_and_play` - 新方法，章节模式转换

## 下一步

1. **运行程序** - `python -m novel_reader --test`
2. **查看调试输出** - 确认书籍被自动选中
3. **点击章节** - 应该自动开始转换
4. **等待转换完成** - 自动开始播放

## 预期体验

```
用户操作：
1. 启动程序
   → 自动选中第一本书

2. 点击第一章
   → 自动开始转换第一章
   → 转换完成后自动播放
   → 后台继续转换后续章节

3. 享受听书！
```
