"""
核心数据模型 - Production级有声书播放器

完整的数据模型定义，支持播放器的所有功能
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Any, Dict
from pathlib import Path
import time


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
    ERROR = auto()


@dataclass
class TextChunk:
    """
    最小逻辑单元 - Chunk

    这是播放器的最小单位，包含：
    - 文本内容
    - 所属章节
    - 音频信息
    - 状态追踪
    """
    chunk_id: int
    chapter_id: int
    text: str

    # 音频相关
    audio_path: Optional[str] = None
    duration_ms: Optional[int] = None
    sample_rate: int = 22050
    channels: int = 1

    # 状态
    status: ChunkStatus = ChunkStatus.PENDING

    # 元数据
    created_at: float = field(default_factory=time.time)
    tts_started_at: Optional[float] = None
    tts_finished_at: Optional[float] = None

    @property
    def has_audio(self) -> bool:
        """是否有音频文件"""
        if not self.audio_path:
            return False
        return Path(self.audio_path).exists()

    @property
    def audio_size_bytes(self) -> int:
        """音频文件大小"""
        if not self.audio_path:
            return 0
        return Path(self.audio_path).stat().st_size if Path(self.audio_path).exists() else 0

    @property
    def is_ready(self) -> bool:
        """是否准备好播放"""
        return self.status == ChunkStatus.READY and self.has_audio

    @property
    def is_done(self) -> bool:
        """是否已播放完成"""
        return self.status == ChunkStatus.DONE

    @property
    def text_length(self) -> int:
        """文本长度"""
        return len(self.text)

    def mark_tts_started(self):
        """标记TTS开始"""
        self.status = ChunkStatus.TTS
        self.tts_started_at = time.time()

    def mark_ready(self, audio_path: str, duration_ms: int):
        """标记为就绪"""
        self.status = ChunkStatus.READY
        self.audio_path = audio_path
        self.duration_ms = duration_ms
        self.tts_finished_at = time.time()

    def mark_playing(self):
        """标记为播放中"""
        self.status = ChunkStatus.PLAYING

    def mark_done(self):
        """标记为已完成"""
        self.status = ChunkStatus.DONE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "chunk_id": self.chunk_id,
            "chapter_id": self.chapter_id,
            "text": self.text,
            "audio_path": self.audio_path,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
        }

    def __repr__(self) -> str:
        return f"Chunk(id={self.chunk_id}, status={self.status.value}, text_len={self.text_length})"


@dataclass
class Chapter:
    """
    章节 - 包含多个chunk

    章节是书的组织单位，包含：
    - 章节信息（ID、标题）
    - chunk列表
    - 位置信息
    """
    chapter_id: int
    title: str
    chunks: List[TextChunk] = field(default_factory=list)

    # 位置信息（在全书中的chunk索引）
    start_index: int = 0
    end_index: int = 0

    @property
    def chunk_count(self) -> int:
        """chunk数量"""
        return len(self.chunks)

    @property
    def total_duration_ms(self) -> int:
        """总时长（毫秒）"""
        return sum(c.duration_ms or 0 for c in self.chunks if c.duration_ms)

    @property
    def total_text_length(self) -> int:
        """总文本长度"""
        return sum(c.text_length for c in self.chunks)

    @property
    def ready_chunks(self) -> int:
        """已准备好的chunk数量"""
        return sum(1 for c in self.chunks if c.is_ready)

    @property
    def done_chunks(self) -> int:
        """已完成的chunk数量"""
        return sum(1 for c in self.chunks if c.is_done)

    @property
    def is_fully_ready(self) -> bool:
        """所有chunk是否都准备好"""
        return len(self.chunks) > 0 and all(c.is_ready for c in self.chunks)

    @property
    def progress_percent(self) -> float:
        """转换进度百分比"""
        if len(self.chunks) == 0:
            return 0.0
        ready = sum(1 for c in self.chunks if c.is_ready or c.is_done)
        return (ready / len(self.chunks)) * 100

    def get_chunk(self, local_index: int) -> Optional[TextChunk]:
        """通过本地索引获取chunk"""
        if 0 <= local_index < len(self.chunks):
            return self.chunks[local_index]
        return None

    def __repr__(self) -> str:
        return f"Chapter(id={self.chapter_id}, title='{self.title}', chunks={len(self.chunks)})"


@dataclass
class Book:
    """
    书籍 - 包含多个章节

    书籍是顶层容器，包含：
    - 书籍信息
    - 章节列表
    - 播放状态
    """
    book_id: int
    title: str
    chapters: List[Chapter] = field(default_factory=list)
    file_path: str = ""

    # 播放状态
    current_chunk_index: int = 0
    last_played_at: Optional[float] = None

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

    @property
    def total_duration_ms(self) -> int:
        """总时长"""
        return sum(ch.total_duration_ms for ch in self.chapters)

    def get_chunk_by_index(self, index: int) -> Optional[TextChunk]:
        """通过全局索引获取chunk"""
        for ch in self.chapters:
            if ch.start_index <= index < ch.end_index:
                local_index = index - ch.start_index
                return ch.get_chunk(local_index)
        return None

    def get_chapter_by_index(self, index: int) -> Optional[Chapter]:
        """通过索引获取章节"""
        if 0 <= index < len(self.chapters):
            return self.chapters[index]
        return None

    def find_chapter_by_chunk_id(self, chunk_id: int) -> Optional[Chapter]:
        """通过chunk ID查找所属章节"""
        for ch in self.chapters:
            if ch.start_index <= chunk_id < ch.end_index:
                return ch
        return None

    def __repr__(self) -> str:
        return f"Book(id={self.book_id}, title='{self.title}', chapters={len(self.chapters)}, total_chunks={self.total_chunks})"


@dataclass
class TTSConfig:
    """TTS配置"""
    # Piper路径
    piper_bin: str = "piper"

    # 模型配置（新方式）
    chinese_model_id: str = "xiao_ya"  # 中文模型 ID
    english_model_id: str = "amy"  # 英文模型 ID

    # 旧版配置（保留用于向后兼容）
    model_path: str = ""
    config_path: str = ""

    # 合成参数
    voice: str = "default"
    speed: float = 1.0

    # 音频参数
    sample_rate: int = 22050
    channels: int = 1

    # 性能参数
    batch_size: int = 3  # 每次合成的chunk数

    def __post_init__(self):
        if not self.model_path:
            # 自动查找模型（旧版兼容）
            try:
                from novel_reader.core.tts import find_model_file
                from novel_reader.core.model_config import get_model

                # 尝试使用新方式加载中文模型
                model = get_model(self.chinese_model_id)
                if model:
                    from novel_reader.core.model_downloader import find_model_file
                    model_path = find_model_file(model.model_filename)
                    if model_path:
                        self.model_path = str(model_path)
                        # 查找配置文件
                        config_path = find_model_file(model.config_name)
                        self.config_path = str(config_path) if config_path else ""
            except ImportError:
                pass

    @property
    def is_valid(self) -> bool:
        """配置是否有效"""
        return bool(self.model_path) and Path(self.model_path).exists()

    def get_model_for_language(self, language: str) -> tuple:
        """
        根据语言获取模型路径和配置路径

        Args:
            language: "zh" 或 "en"

        Returns:
            (model_path, config_path) 元组
        """
        from novel_reader.core.model_config import get_model
        from novel_reader.core.model_downloader import find_model_file

        model_id = self.chinese_model_id if language == "zh" else self.english_model_id
        model = get_model(model_id)

        if not model:
            # 回退到旧配置
            return self.model_path, self.config_path

        model_path = find_model_file(model.model_filename)
        config_path = find_model_file(model.config_name)

        if not model_path:
            # 回退到旧配置
            return self.model_path, self.config_path

        return str(model_path), str(config_path) if config_path else ""


@dataclass
class PlayerConfig:
    """播放器配置"""
    # 文本处理
    chunk_size: int = 100  # 目标chunk大小（字数）
    min_chunk_size: int = 50  # 最小chunk大小
    max_chunk_size: int = 200  # 最大chunk大小

    # TTS调度
    prefetch_chunks: int = 2  # 预取chunk数量
    tts_batch_chunks: int = 3  # 每批TTS处理数量
    max_tts_queue: int = 5  # TTS队列最大长度

    # 缓存
    audio_cache_size: int = 80  # 音频缓存大小

    # 播放
    first_chunk_timeout: int = 120000  # 首个chunk超时（毫秒）- 增加到120秒以等待TTS转换
    auto_play_next_chapter: bool = True  # 自动播放下一章

    # 性能
    tts_timeout: int = 600  # 单个TTS超时（秒）- 增加到10分钟

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chunk_size": self.chunk_size,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "prefetch_chunks": self.prefetch_chunks,
            "tts_batch_chunks": self.tts_batch_chunks,
            "max_tts_queue": self.max_tts_queue,
            "audio_cache_size": self.audio_cache_size,
            "first_chunk_timeout": self.first_chunk_timeout,
            "auto_play_next_chapter": self.auto_play_next_chapter,
        }


# 默认配置
DEFAULT_CONFIG = PlayerConfig()
