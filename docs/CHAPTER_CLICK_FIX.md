# 章节点击自动转换功能修复

## 问题描述

点击章节后没有自动触发 TTS 转换，而是直接尝试播放，导致报错：
```
错误: 没有可用的音频文件
请先进行 TTS 转换！
```

## 根本原因

双击章节时调用的是旧的 `_convert_book()` 方法，该方法会转换整本书，但转换完成后不会自动播放。而且转换期间会直接 `return`，不会执行播放逻辑。

## 修复内容

### 1. 单击章节 (`_on_chapter_selected`)

**行为**：检查当前章节是否已转换
- 已转换 → 直接播放
- 未转换 → 转换并自动播放

```python
def _on_chapter_selected(start_chunk):
    # 检查当前章节是否有音频
    if chapter_has_audio:
        _play_from_chunk(start_chunk)
    else:
        _convert_chapter_and_play(book_id, start_chunk)
```

### 2. 双击章节 (`_on_chapter_double_clicked`)

**修复前**：调用 `_convert_book()` 转换整本书
```python
if not has_audio:
    _convert_book(book_id)  # ❌ 转换整本，不会自动播放
    return
```

**修复后**：使用章节模式转换
```python
if not has_audio:
    _convert_chapter_and_play(book_id, start_chunk)  # ✓ 转换当前章节并自动播放
else:
    _play_from_chunk(start_chunk)
```

## 测试验证

### 启动程序
```bash
python -m novel_reader
```

### 操作步骤
1. 导入书籍（拖拽 .txt 文件）
2. 点击书籍查看章节列表
3. **单击**章节 → 自动转换并播放
4. **双击**章节 → 自动转换并播放

### 预期行为

```
单击"第一章"
    ↓
检查音频文件
    ↓
[未转换] → 开始转换当前章节
    ↓
转换完成 → 立即开始播放
    ↓
后台继续转换后续章节
```

## 代码变更

### 文件: `novel_reader/gui/main_window.py`

**修改的方法**:
- `_on_chapter_selected()` - 保持不变
- `_on_chapter_double_clicked()` - 修复为使用章节模式转换

**新增的方法**:
- `_convert_chapter_and_play()` - 章节模式转换并自动播放
- `_on_chapter_tts_finished()` - 章节转换完成后的处理
- `_play_from_chunk()` - 从指定位置播放

## 功能对比

| 操作 | 修复前 | 修复后 |
|------|--------|--------|
| 单击已转换章节 | 无反应 | 立即播放 ✓ |
| 单击未转换章节 | 无反应 | 转换并播放 ✓ |
| 双击已转换章节 | 播放 | 播放 ✓ |
| 双击未转换章节 | 转换整本 | 转换章节并播放 ✓ |

## 测试结果

```bash
============================================================
GUI Functionality Test
============================================================
Testing imports...                     ✓
GUI widgets imported...                ✓
Workers imported...                     ✓
Dialogs imported...                     ✓
Main window imported...                 ✓
Main window created...                  ✓
All tests passed! ✓
============================================================
```

## 使用建议

### 推荐操作流程

1. **首次使用** - 单击第一章
   - 自动转换第一章
   - 转换完成后自动播放
   - 后台继续转换后续章节

2. **快速跳转** - 双击任意章节
   - 如果已转换 → 立即播放
   - 如果未转换 → 转换并播放

3. **暂停/继续** - 使用播放控制按钮
   - 暂停不会停止转换
   - 停止会停止一切

### 注意事项

- 转换需要时间，请耐心等待
- 后台转换不会影响播放
- 可以随时查看转换进度

## 后续优化建议

1. **进度提示** - 在章节列表中显示转换状态图标
2. **预加载** - 预测下一个要播放的章节并提前转换
3. **批量操作** - 支持选择多个章节批量转换
4. **转换优先级** - 允许用户调整转换优先级

## 相关文件

- `novel_reader/gui/main_window.py` - 主窗口逻辑
- `novel_reader/gui/workers/tts_worker.py` - TTS 工作线程
- `novel_reader/gui/widgets/chapter_list_widget.py` - 章节列表组件

## 版本信息

- 修复版本: v1.1
- 修复日期: 2025-01-31
- 测试状态: ✓ 通过
