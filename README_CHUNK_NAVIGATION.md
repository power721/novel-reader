# 分段导航功能

## 功能概述

添加了分段级别的精细导航功能，允许用户逐个分段（chunk）前进或后退，补充了现有的章节级导航。

## 实现细节

### 1. PlayerWidget更新 (`novel_reader/gui/widgets/player_widget.py`)

**新增按钮:**
```python
self.prev_chunk_btn = QPushButton("◀ 上一分段")
self.next_chunk_btn = QPushButton("下一分段 ▶")
```

**新增信号:**
```python
play_previous_chunk_requested = Signal()  # 请求播放上一分段
play_next_chunk_requested = Signal()      # 请求播放下一分段
```

**UI布局:**
```
┌─────────────────────────────────┐
│  ▶️ 播放控制                     │
├─────────────────────────────────┤
│ 📖 正在播放: 书名 - 章节        │
├─────────────────────────────────┤
│  [⏮ 上一章] [▶ 播放] [⏹ 停止] [⏭ 下一章]  │
│         [◀ 上一分段] 分段导航 [下一分段 ▶]  │
├─────────────────────────────────┤
│  播放进度: [========--] 100/200 │
└─────────────────────────────────┘
```

### 2. MainWindow实现 (旧版)

**新增方法:**

#### `_play_next_chunk()`
- 获取当前chunk位置
- 计算下一个chunk (+1)
- 检查边界（是否到达最后一个分段）
- 检查音频文件是否存在
- 跳转并播放或转换

#### `_play_previous_chunk()`
- 获取当前chunk位置
- 计算上一个chunk (-1)
- 检查边界（是否到达第一个分段）
- 检查音频文件是否存在
- 跳转并播放或转换

**信号连接:**
```python
self.player_widget.play_previous_chunk_requested.connect(self._play_previous_chunk)
self.player_widget.play_next_chunk_requested.connect(self._play_next_chunk)
```

### 3. MainWindow V2实现 (新版)

使用新架构的PlaybackController:

```python
def _play_next_chunk(self):
    """播放下一个分段"""
    # 获取当前chunk位置
    current_chunk = book['current_chunk']
    next_chunk = current_chunk + 1

    # 边界检查
    if next_chunk >= total_chunks:
        QMessageBox.information(self, "提示", "已经是最后一个分段了")
        return

    # 使用PlaybackController跳转
    self.playback_adapter.seek_to_chunk(next_chunk)

    # 如果未播放，开始播放
    if not self.playback_adapter.is_playing:
        self.playback_adapter.play()
```

## 使用方法

### GUI操作

1. **播放下一分段**
   - 点击 "下一分段 ▶" 按钮
   - 自动跳转到下一个chunk并播放

2. **播放上一分段**
   - 点击 "◀ 上一分段" 按钮
   - 自动跳转到上一个chunk并播放

### 导航层级对比

| 导航类型 | 按钮 | 跳转范围 | 用途 |
|---------|------|---------|------|
| 分段导航 | ◀ 上一分段 / 下一分段 ▶ | ±1 chunk | 精细调整位置 |
| 章节导航 | ⏮ 上一章 / ⏭ 下一章 | 跳转到章节边界 | 快速章节切换 |

### 典型使用场景

**场景1: 重复听取**
- 听完某个精彩段落，想再听一遍
- 点击 "◀ 上一分段" 即可

**场景2: 跳过内容**
- 某个分段不感兴趣，快速跳过
- 点击 "下一分段 ▶" 继续

**场景3: 精确定位**
- 结合章节导航快速到达大致位置
- 使用分段导航精细调整到准确位置

## 边界处理

### 到达第一个分段
```
状态: 当前chunk = 0
操作: 点击 "◀ 上一分段"
结果: 提示 "已经是第一个分段了"
```

### 到达最后一个分段
```
状态: 当前chunk = total_chunks - 1
操作: 点击 "下一分段 ▶"
结果: 提示 "已经是最后一个分段了"
```

## 音频文件处理

### 已转换的chunk
- 直接跳转播放
- 状态栏显示 "跳转到分段 X"

### 未转换的chunk
- 自动触发TTS转换
- 转换完成后自动播放
- 状态栏显示 "转换分段 X"

## 测试

### 运行测试套件

```bash
python novel_examples/test_chunk_navigation.py
```

### 测试覆盖

✅ **PlayerWidget测试**
- 按钮存在性验证
- 信号存在性验证
- UI元素正确性

✅ **信号连接测试**
- 信号发射正确性
- 槽函数触发验证

✅ **MainWindow集成测试**
- 方法存在性验证
- 旧版架构兼容性

✅ **MainWindow V2集成测试**
- 新架构适配性
- PlaybackController集成

### 测试结果

```
✅ 所有测试通过!

✓ PlayerWidget 测试通过
✓ 信号连接测试通过
✓ MainWindow 集成测试通过
✓ MainWindow V2 集成测试通过
```

## 文件清单

### 修改文件
- `novel_reader/gui/widgets/player_widget.py` - 添加按钮和信号
- `novel_reader/gui/main_window.py` - 实现旧版处理逻辑
- `novel_reader/gui/main_window_v2.py` - 实现新版处理逻辑

### 新增文件
- `novel_examples/test_chunk_navigation.py` - 功能测试套件
- `README_CHUNK_NAVIGATION.md` - 功能说明文档（本文件）

## 快捷键建议

可选的键盘快捷键增强:

| 快捷键 | 功能 | 说明 |
|-------|------|-----|
| Alt + ← | 上一分段 | 向后一个chunk |
| Alt + → | 下一分段 | 向前一个chunk |
| Ctrl + ← | 上一章 | 向后一个章节 |
| Ctrl + → | 下一章 | 向前一个章节 |

## 设计考虑

### 1. 分段 vs 章节

**分段 (Chunk):**
- 最小的音频单位
- 通常80-120字
- 适合精确控制

**章节 (Chapter):**
- 逻辑内容单元
- 包含多个chunk
- 适合快速导航

### 2. UI布局

分段导航按钮放置在章节导航按钮下方，形成两级导航：
- 第一行: 章节级（大跳转）
- 第二行: 分段级（微调）

### 3. 状态反馈

- 边界情况提示用户
- 音频状态显示在状态栏
- 播放器状态实时更新

## 与现有功能的集成

### 自动播放下一章节
- 章节播放完成后自动触发
- 不受分段导航影响
- 仍可使用分段导航手动跳转

### 播放历史记录
- 分段跳转会更新current_chunk
- 历史记录准确保存最后位置
- 下次打开从上次位置继续

### 章节高亮
- 分段导航会更新章节高亮
- 跨章节跳转时自动切换章节
- UI保持同步

## 性能考虑

### 音频检查
- 每次跳转检查音频文件
- 文件不存在时触发TTS
- 已存在文件直接播放

### 转换优先级
- 手动跳转优先级最高
- 打断后台转换任务
- 立即响应用户操作

## 未来增强

可选的功能改进:

1. **批量跳转**: 支持跳转N个分段
2. **进度条拖拽**: 直接拖动到指定位置
3. **快捷键支持**: 添加键盘快捷键
4. **分段预览**: 显示分段文本内容
5. **跳转历史**: 记录跳转历史，支持前进/后退

## 兼容性

- ✅ 旧版MainWindow (PlaybackWorker架构)
- ✅ 新版MainWindow V2 (PlaybackController架构)
- ✅ 现有数据库（无需迁移）
- ✅ 现有播放功能
