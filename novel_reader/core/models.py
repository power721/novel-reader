"""
核心数据模型 - 播放器架构
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List
from pathlib import Path


class ChunkStatus(Enum):
    """Chunk状态"""
    PENDING = "pending"     # 未处理
    TTS = "tts"            # 合成中
    READY = "ready"        # 音频已就绪
    PLAYING = "playing"    # 播放中
    DONE = "done"          # 已播放完成


class PlaybackState(Enum):
    """播放器状态"""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    SEEKING = auto()


@dataclass
class TextChunk:
    """
    最小逻辑单元 - Chunk

    一个chunk包含：
    - 文本内容
    - 所属章节
    - 音频文件路径（如果有）
    - 音频时长（如果有）
    - 当前状态
    """
    chunk_id: int
    chapter_id: int
    text: str

    audio_path: Optional[str] = None
    duration_ms: Optional[int] = None
    status: ChunkStatus = ChunkStatus.PENDING

    @property
    def has_audio(self) -> bool:
        """是否有音频文件"""
        return self.audio_path is not None and Path(self.audio_path).exists()

    @property
    def is_ready(self) -> bool:
        """是否准备好播放"""
        return self.status == ChunkStatus.READY and self.has_audio

    def __repr__(self) -> str:
        return f"Chunk({self.chunk_id}, {self.status.value}, text_len={len(self.text)})"


@dataclass
class Chapter:
    """
    章节 - 包含多个chunk

    章节包含：
    - 章节ID
    - 标题
    - chunk列表
    - 起始位置（在全书中的位置）
    """
    chapter_id: int
    title: str
    chunks: List[TextChunk] = field(default_factory=list)

    # 起始位置（在整个书中的chunk索引）
    start_index: int = 0
    end_index: int = 0  # 不包含

    @property
    def chunk_count(self) -> int:
        """chunk数量"""
        return len(self.chunks)

    @property
    def total_duration_ms(self) -> int:
        """总时长（毫秒）"""
        return sum(c.duration_ms or 0 for c in self.chunks)

    @property
    def ready_chunks(self) -> int:
        """已准备好的chunk数量"""
        return sum(1 for c in self.chunks if c.is_ready)

    @property
    def is_fully_ready(self) -> bool:
        """所有chunk是否都准备好"""
        return all(c.is_ready for c in self.chunks)

    def __repr__(self) -> str:
        return f"Chapter({self.chapter_id}, '{self.title}', chunks={len(self.chunks)})"


@dataclass
class Book:
    """
    书籍 - 包含多个章节

    书籍包含：
    - 书籍ID
    - 标题
    - 章节列表
    - 文件路径
    - 当前播放位置
    """
    book_id: int
    title: str
    chapters: List[Chapter] = field(default_factory=list)
    file_path: str = ""

    # 当前播放位置（chunk索引）
    current_chunk_index: int = 0

    @property
    def total_chunks(self) -> int:
        """总chunk数"""
        return sum(ch.chunk_count for ch in self.chapters)

    @property
    def total_chapters(self) -> int:
        """总章节数"""
        return len(self.chapters)

    @property
    def current_chapter(self) -> Optional[Chapter]:
        """当前章节"""
        for ch in self.chapters:
            if ch.start_index <= self.current_chunk_index < ch.end_index:
                return ch
        return None

    @property
    def progress_percent(self) -> float:
        """播放进度百分比"""
        if self.total_chunks == 0:
            return 0.0
        return (self.current_chunk_index / self.total_chunks) * 100

    def get_chunk_by_index(self, index: int) -> Optional[TextChunk]:
        """通过全局索引获取chunk"""
        for ch in self.chapters:
            if ch.start_index <= index < ch.end_index:
                local_index = index - ch.start_index
                if 0 <= local_index < len(ch.chunks):
                    return ch.chunks[local_index]
        return None

    def __repr__(self) -> str:
        return f"Book({self.book_id}, '{self.title}', chapters={len(self.chapters)})"


@dataclass
class TTSConfig:
    """TTS配置"""
    piper_bin: str = "piper"
    model_path: str = ""
    config_path: str = ""
    voice: str = "default"
    speed: float = 1.0

    # 合成参数
    sample_rate: int = 22050
    channels: int = 1

    def __post_init__(self):
        if not self.model_path:
            # 自动查找模型
            from novel_reader.core.tts import auto_detect_model
            model, config = auto_detect_model()
            if model:
                self.model_path = model
                self.config_path = config or ""


# 播放器配置（默认参数）
AUDIOBOOK_CONFIG = {
    "text_chunk_size": 100,          # 每个chunk约100字
    "tts_batch_chunks": 3,           # 每批TTS处理3个chunk
    "prefetch_chunks": 2,            # 预取2个chunk
    "audio_cache_size": 80,          # 音频缓存80个chunk
    "max_tts_queue": 5,              # TTS队列最多5个任务
    "first_chunk_timeout": 3000,     # 首个chunk超时3秒
}
