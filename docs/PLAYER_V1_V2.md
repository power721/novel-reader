# Player V1 vs V2 架构对比

## 概述

项目目前有两个播放器架构：V1（当前使用）和 V2（新架构，未来方向）。

---

## V1 架构 (PlaybackWorker)

**位置**: `novel_reader/gui/workers/playback_worker.py`

### 特点

- **简单直接**: 基于 QThread 的单线程实现
- **顺序播放**: 从头到尾顺序播放 chunk
- **等待机制**: 等待 TTS 转换完成才播放
- **数据库驱动**: 使用 SQLite 存储书籍和章节信息

### 代码结构

```python
class PlaybackWorker(QThread):
    # 信号
    finished = Signal()
    error = Signal(str)
    progress_updated = Signal(int, int)

    def run(self):
        # 获取书籍信息
        book = get_book(self.book_id)
        text = load_txt_file(book['file_path'])
        chunks, _ = parse_txt(text)

        # 顺序播放循环
        for chunk_id in range(start, total_chunks):
            # 1. 检查音频是否存在
            if not audio_path.exists():
                # 等待转换完成
                self.chunks_conversion_requested.emit([chunk_id])

            # 2. 预转换后续 chunks
            self.chunks_conversion_requested.emit([chunk_id+1, chunk_id+2, ...])

            # 3. 播放音频
            play_audio(str(audio_path))

            # 4. 清理旧文件
            self._cleanup_old_chunks(chunk_id, book_audio_dir)
```

### 优点

- ✅ 简单易懂，逻辑直观
- ✅ 适合顺序播放场景
- ✅ 代码维护成本低

### 缺点

- ❌ 没有完整的状态机
- ❌ Seek 功能受限（无法精确到毫秒）
- ❌ 线程安全性不足
- ❌ 缓存策略简单
- ❌ 调度机制不灵活

---

## V2 架构 (PlaybackController)

**位置**: `novel_reader/core/playback_controller_v2.py`

### 特点

- **事件驱动**: 基于 Queue 的事件循环
- **完整状态机**: STOPPED/PLAYING/PAUSED/SEEKING
- **模块化设计**: 多个独立组件协作
- **优先级调度**: URGENT > HIGH > NORMAL > LOW
- **LRU 缓存**: 智能缓存管理
- **精确 Seek**: 支持毫秒级定位

### 核心组件

```python
# 1. 数据模型
class Book, Chapter, TextChunk, PlaybackState

# 2. ChunkManager - 文本解析和分块
class ChunkManager:
    def parse_book(file_path, book_id) -> Book
    def get_audio_path(book_id, chunk_id) -> str

# 3. AudioCache - LRU 缓存
class AudioCache:
    def get(key) -> Optional[Path]
    def put(key, value) -> None

# 4. TTSScheduler - TTS 调度器
class TTSScheduler:
    def schedule_chunk(chunk, priority=TaskPriority.NORMAL)
    def schedule_chapter(chapter)

# 5. AudioPlayer - 音频播放
class AudioPlayer:
    def play(audio_path, start_offset_ms=0)
    def seek(offset_ms)

# 6. PlaybackController - 核心控制器
class PlaybackController:
    def load_book(book_id, file_path)
    def play()
    def pause()
    def seek(chunk_index, offset_ms)
    def next_chapter()
```

### 代码结构

```python
class PlaybackController:
    def __init__(self):
        # 组件初始化
        self.chunk_manager = ChunkManager()
        self.audio_cache = AudioCache()
        self.audio_player = AudioPlayer()
        self.tts_scheduler = TTSScheduler()

        # 状态管理
        self.state = PlaybackState.STOPPED
        self.event_queue = Queue()

    def _event_loop(self):
        """事件处理循环（独立线程）"""
        while self._running:
            event = self.event_queue.get()
            self._handle_event(event)

    def play(self):
        """发送播放事件"""
        self._post_event(PlayerEvent.PLAY)

    def _handle_play(self):
        """处理播放事件"""
        # 1. 获取当前 chunk
        # 2. 检查音频缓存
        # 3. 调度 TTS（如果需要）
        # 4. 播放音频
        # 5. 调度后续 chunks
        # 6. 清理旧文件
        self._cleanup_old_chunks()
```

### 优点

- ✅ 完整的状态机，逻辑清晰
- ✅ 事件驱动，扩展性强
- ✅ 优先级调度，智能预取
- ✅ LRU 缓存，性能优化
- ✅ 精确 Seek，用户体验好
- ✅ 线程安全，无竞态条件
- ✅ 模块化设计，易于测试

### 缺点

- ❌ 代码复杂度较高
- ❌ 需要理解事件驱动架构
- ❌ 尚未完全集成到 GUI

---

## 功能对比表

| 功能 | V1 (PlaybackWorker) | V2 (PlaybackController) |
|------|---------------------|--------------------------|
| **状态管理** | 简单标志 | 完整状态机 |
| **播放控制** | play/pause/stop | play/pause/stop/seek |
| **Seek 精度** | chunk 级别 | 毫秒级别 |
| **TTS 调度** | 信号机制 | 优先级队列 |
| **缓存策略** | 简单文件检查 | LRU 缓存 |
| **预取机制** | 固定数量 | 智能调度 |
| **线程模型** | 单线程 QThread | 多线程 + 事件队列 |
| **章节跳转** | 支持 | 支持 + 优化 |
| **错误处理** | 基础 | 完善 |
| **扩展性** | 低 | 高 |
| **测试性** | 低 | 高 |

---

## 当前状态

### V1 (生产使用)
- ✅ 完全集成到 GUI
- ✅ 所有功能正常工作
- ✅ 稳定可靠
- ✅ 已添加音频清理功能

### V2 (开发中)
- ✅ 核心组件已实现
- ✅ 功能完整
- ⚠️ 尚未完全集成到 GUI
- ⚠️ 需要更多测试

---

## 迁移计划

### 短期 (V1 优化)
- ✅ 添加音频清理功能（已完成）
- ⏳ 改进缓存策略
- ⏳ 优化 TTS 调度

### 中期 (V2 集成)
- ⏳ GUI 适配器层
- ⏳ 数据库兼容
- ⏳ 平滑迁移路径

### 长期 (完全迁移)
- ⏳ 弃用 V1
- ⏳ V2 成为唯一架构

---

## 使用建议

### 何时使用 V1
- 当前 GUI 应用
- 简单播放场景
- 不需要高级功能

### 何时使用 V2
- 新功能开发
- 需要精确 Seek
- 需要更好的性能
- 需要更好的扩展性

---

## 代码示例对比

### V1: 播放一个 chunk
```python
# 检查音频是否存在
if not audio_path.exists():
    self.chunks_conversion_requested.emit([chunk_id])
    # 等待转换完成...

# 播放音频
play_audio(str(audio_path))
```

### V2: 播放一个 chunk
```python
# 检查缓存
if not audio_cache.has(chunk_id):
    # 调度 TTS（优先级：URGENT）
    tts_scheduler.schedule_chunk(chunk, TaskPriority.URGENT)

# 等待就绪后播放
audio_player.play(audio_path, on_finished=self._on_chunk_finished)

# 自动调度后续 chunks
self._schedule_next_chunks()

# 自动清理旧文件
self._cleanup_old_chunks()
```

---

## 总结

| 方面 | V1 | V2 |
|------|----|----|
| **成熟度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **性能** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **扩展性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **维护性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**当前推荐**: 使用 V1，因为它稳定可靠且完全集成。V2 是未来方向，待集成后将成为主要架构。
