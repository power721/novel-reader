# Novel Reader - 更新日志

## 最新改进

### 1. 播放前音频文件检查

**问题**：直接点击播放时，如果未进行 TTS 转换，会跳过所有音频文件。

**解决方案**：
- 播放器现在会在开始播放前检查是否有可用的音频文件
- 如果没有音频文件，会提示用户先进行 TTS 转换
- 显示可用的音频文件数量

**改进位置**：
- `novel_reader/core/player.py:play_book()`
- `novel_reader/gui/main_window.py:_check_audio_files()`

### 2. GUI 智能播放提示

**问题**：用户不知道书籍是否已转换音频。

**解决方案**：
- 点击播放按钮时，自动检查音频文件
- 如果未转换，弹出对话框询问是否立即开始转换
- 显示已转换的音频数量

**改进位置**：
- `novel_reader/gui/main_window.py:_play_book()`
- `novel_reader/gui/main_window.py:_on_chapter_double_clicked()`

### 3. 章节点击自动 TTS 转换

**新功能**：点击章节自动开始 TTS 转换

**行为**：
- 点击章节时，如果该书未进行 TTS 转换
- 自动触发 TTS 转换（带 100ms 延迟防止频繁点击）
- 状态栏显示转换状态

**改进位置**：
- `novel_reader/gui/widgets/chapter_list_widget.py` - 新增 `chapter_selected` 信号
- `novel_reader/gui/main_window.py:_on_chapter_selected()` - 新增处理方法

### 4. 播放器改进

**控制台输出示例**：
```
开始播放: 《警门赘婿》01_228连载_作品作者：卡牌（写书还债）
起始位置: chunk 21 / 748
可用音频: 0 / 727
按 Ctrl+C 停止播放

错误: 没有可用的音频文件
请先进行 TTS 转换！
提示: 在 GUI 中选择书籍后点击「转换整本书」按钮
```

## 使用流程

### 完整的播放流程

1. **导入书籍**
   - 拖拽 `.txt` 文件到窗口
   - 或使用菜单「文件 → 导入书籍」

2. **选择书籍**
   - 点击书籍列表中的书籍
   - 章节列表和书签列表会自动加载

3. **TTS 转换**
   - 方式一：点击「转换整本书」按钮
   - 方式二：点击任意章节自动触发转换
   - 查看实时转换日志和进度

4. **播放音频**
   - 双击书籍/章节/书签播放
   - 或点击「▶ 播放」按钮
   - 播放进度自动保存

## 文件变更

### 修改的文件

```
novel_reader/
├── core/player.py                    # 添加音频文件检查
├── gui/
│   ├── main_window.py                # 添加智能播放提示
│   └── widgets/
│       └── chapter_list_widget.py    # 添加章节点击信号
```

### 新增功能

- ✅ 播放前自动检查音频文件
- ✅ 未转换时提示并询问是否转换
- ✅ 点击章节自动触发 TTS 转换
- ✅ 显示可用音频数量
- ✅ 更友好的错误提示

## 测试

运行测试脚本验证所有功能：

```bash
python test_gui.py
```

所有测试通过 ✓

## 运行

```bash
# 启动 GUI
python -m novel_reader

# 或带测试数据
python -m novel_reader --test
```
