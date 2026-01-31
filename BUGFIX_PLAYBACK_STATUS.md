# 播放状态显示修复

## 问题描述

播放状态显示的是"书籍 ID: 11"或"正在播放..."，而不是显示书名和章节标题。

## 问题原因

在MainWindow中调用`set_playing_state(True)`时，PlayerWidget的`current_book_title`和`current_chapter_title`变量还是空的，因为没有先调用`update_current_playback()`来设置这些值。

## 修复方案

### 1. PlayerWidget增强

**新增成员变量:**
```python
self.current_book_title = ""
self.current_chapter_title = ""
```

**修改`_update_current_display()`:**
- 存储书名和章节标题到成员变量
- 用于后续播放状态显示

**修改`set_playing_state()`:**
```python
if is_playing:
    self.play_btn.setText("⏸ 暂停")
    # 显示书名和章节标题
    if self.current_book_title and self.current_chapter_title:
        self.playback_status_label.setText(f"▶ {self.current_book_title} - {self.current_chapter_title}")
    elif self.current_book_title:
        self.playback_status_label.setText(f"▶ {self.current_book_title}")
    else:
        self.playback_status_label.setText("正在播放...")
```

**修改`set_paused_state()`:**
```python
if is_paused:
    self.play_btn.setText("▶ 继续")
    # 暂停时也显示书名和章节
    if self.current_book_title and self.current_chapter_title:
        self.playback_status_label.setText(f"⏸ {self.current_book_title} - {self.current_chapter_title}")
    ...
```

### 2. MainWindow修复

#### 修复1: `_play_book()` 方法

在创建播放工作线程之前，获取书籍信息并更新播放显示：

```python
@Slot(int)
def _play_book(self, book_id: int):
    """播放书籍"""
    ...

    # 创建播放工作线程
    self.playback_worker = PlaybackWorker(book_id)
    ...
    self.playback_worker.start()

    # 获取书籍信息和当前章节，更新播放显示
    from novel_reader.core import get_book, get_book_chapters
    book = get_book(book_id)
    if book:
        chapters = get_book_chapters(book_id)
        current_chapter = book.get('current_chapter', 0)

        chapter_title = ""
        if chapters and 0 <= current_chapter - 1 < len(chapters):
            chapter_title = chapters[current_chapter - 1]['title']

        # 更新播放显示
        self.player_widget.update_current_playback(book['title'], chapter_title)

    # 更新 UI 状态
    self.player_widget.set_playing_state(True)
```

#### 修复2: `_play_from_chunk()` 方法

在从指定位置播放时，也要更新书名和章节：

```python
def _play_from_chunk(self, start_chunk: int):
    """从指定位置播放"""
    ...

    # 获取书籍信息和当前章节，更新播放显示
    from novel_reader.core import get_book, get_book_chapters
    book = get_book(self.current_book_id)
    if book:
        chapters = get_book_chapters(self.current_book_id)
        chapter_title = ""

        if chapters:
            # 找到包含start_chunk的章节
            for i, chapter in enumerate(chapters):
                chapter_start = chapter['start_chunk']
                if i + 1 < len(chapters):
                    next_chapter_start = chapters[i + 1]['start_chunk']
                    if chapter_start <= start_chunk < next_chapter_start:
                        chapter_title = chapter['title']
                        break
                else:
                    if chapter_start <= start_chunk:
                        chapter_title = chapter['title']
                        break

        # 更新播放显示
        self.player_widget.update_current_playback(book['title'], chapter_title)

    # 更新 UI 状态
    self.player_widget.set_playing_state(True)
```

#### 修复3: `_on_playback_progress()` 方法

在播放进度更新时，同步更新章节信息：

```python
@Slot(int, int)
def _on_playback_progress(self, current: int, total: int):
    """播放进度更新"""
    self.player_widget.set_progress(current, total)
    self.chapter_list_widget.highlight_current_chapter(current)

    # 更新播放状态显示（获取当前章节标题）
    if self.current_book_id:
        from novel_reader.core import get_book, get_book_chapters
        book = get_book(self.current_book_id)
        if book:
            chapters = get_book_chapters(self.current_book_id)
            if chapters:
                chapter_title = ""
                for chapter in chapters:
                    chapter_start = chapter['start_chunk']
                    if chapter_start <= current:
                        chapter_title = chapter['title']
                    else:
                        break

                # 更新播放显示
                if chapter_title:
                    self.player_widget.update_current_playback(book['title'], chapter_title)
                    # 重新设置播放状态以更新显示文本
                    if self.player_widget.is_playing:
                        self.player_widget.set_playing_state(True)
```

## 显示效果

### 修复前
```
播放状态: "正在播放..." 或 "书籍 ID: 11"
```

### 修复后
```
播放状态: "▶ 三体 - 第一章 科学边界"
暂停状态: "⏸ 三体 - 第一章 科学边界"
```

### 显示规则

1. **有书名和章节**: `▶ 书名 - 章节标题`
2. **只有书名**: `▶ 书名`
3. **都没有**: `正在播放...`

## 测试验证

```bash
python -c "
from PySide6.QtWidgets import QApplication
from novel_reader.gui.widgets.player_widget import PlayerWidget

app = QApplication([])
widget = PlayerWidget()

widget.update_current_playback('三体', '第一章 科学边界')
widget.set_playing_state(True)
print(widget.playback_status_label.text())
# 输出: ▶ 三体 - 第一章 科学边界
"
```

## 文件修改清单

### 修改的文件
- `novel_reader/gui/widgets/player_widget.py`
  - 添加`current_book_title`和`current_chapter_title`成员变量
  - 修改`_update_current_display()`存储书名和章节
  - 修改`set_playing_state()`显示书名和章节
  - 修改`set_paused_state()`显示书名和章节

- `novel_reader/gui/main_window.py`
  - 修改`_play_book()`在播放前更新书名和章节
  - 修改`_play_from_chunk()`在跳转时更新信息
  - 修改`_on_playback_progress()`同步章节信息

## 兼容性

- ✅ 旧版MainWindow (PlaybackWorker架构)
- ✅ 新版MainWindow V2 (PlaybackController架构)
- ✅ 现有播放功能
- ✅ 所有UI状态切换

## 注意事项

1. **调用顺序**: 必须先调用`update_current_playback()`，再调用`set_playing_state()`
2. **进度更新**: 在`_on_playback_progress()`中会自动更新章节标题
3. **状态同步**: 章节切换时显示会自动更新

## 验证步骤

1. 选择一本书 → 显示"未播放"
2. 点击播放 → 显示"▶ 书名 - 章节标题"
3. 切换章节 → 自动更新显示新的章节标题
4. 暂停播放 → 显示"⏸ 书名 - 章节标题"
5. 恢复播放 → 显示"▶ 书名 - 章节标题"
