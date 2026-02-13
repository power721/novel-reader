"""
ChunkManager - 文本解析和Chunk管理

Production级实现：
- 智能文本切分（按标点符号，避免句子中间断开）
- 章节识别
- Chunk生命周期管理
"""
import re
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib

from .models_v2 import TextChunk, Chapter, Book, ChunkStatus, PlayerConfig


class ChunkManager:
    """
    Chunk管理器 - 文本解析和切分

    职责：
    1. 加载和解析文本文件
    2. 识别章节标题
    3. 智能切分chunks
    4. 管理音频文件路径
    """

    # 章节标题正则（支持多种格式）
    CHAPTER_PATTERNS = [
        # EPUB/MOBI 转换标记
        re.compile(r'^### CHAPTER ###\s*(.+?)\s*$', re.MULTILINE),
        # 中文格式
        re.compile(r'^(第[零一二三四五六七八九十百千0-9]+[章节回卷集部篇讲].*)$', re.MULTILINE),
        re.compile(r'^([零一二三四五六七八九十百千0-9]+)[、\.](.*)$', re.MULTILINE),
        # 英文/数字格式
        re.compile(r'^(Chapter\s*\d+.*$)', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^第\d+章.*$', re.MULTILINE),
    ]

    # 跳过的章节标题（非正文内容）
    SKIP_CHAPTER_TITLES = {
        '目录', '目次', 'table of contents', 'toc',
        '封面', '封底', '书名页', '版权页',
        '作者简介', '作者介绍', '关于作者',
        '推荐序', '推荐语', '书评',
        '附录', '后记', '跋', '编者按'
    }

    # 句子切分正则（按标点符号）
    SENTENCE_DELIMITERS = re.compile(r'([。！？；!?;]|\n{2,})')

    def __init__(self, config: PlayerConfig = None):
        """
        初始化ChunkManager

        Args:
            config: 播放器配置
        """
        self.config = config or PlayerConfig()

        # 音频输出目录
        self.audio_dir = Path("data/audio")

    def parse_book(self, file_path: str, book_id: int) -> Book:
        """
        解析书籍文件

        Args:
            file_path: 文本文件路径
            book_id: 书籍ID

        Returns:
            Book对象
        """
        # 加载文本
        text = self._load_text(file_path)
        title = Path(file_path).stem

        # 识别章节
        chapters_text = self._split_chapters(text)

        if not chapters_text:
            # 没有章节，整本书作为一章
            chapters_text = [("全文", text)]

        # 为每个章节创建chunks
        chapters = []
        current_index = 0

        for chapter_id, (chapter_title, chapter_text) in enumerate(chapters_text):
            chapter = self._create_chapter(
                chapter_id=chapter_id,
                title=chapter_title,
                text=chapter_text,
                book_id=book_id,
                start_index=current_index
            )
            if chapter.chunk_count > 0:  # 只添加非空章节
                chapters.append(chapter)
                current_index += chapter.chunk_count

        return Book(
            book_id=book_id,
            title=title,
            chapters=chapters,
            file_path=file_path,
            current_chunk_index=0
        )

    def _load_text(self, file_path: str) -> str:
        """
        加载文本文件

        Args:
            file_path: 文件路径

        Returns:
            文本内容
        """
        # 尝试UTF-8编码
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 回退到GBK
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()

    def _split_chapters(self, text: str) -> List[Tuple[str, str]]:
        """
        识别章节并切分文本

        Returns:
            [(章节标题, 章节文本), ...]
        """
        # 使用所有模式查找章节标题
        all_matches = []
        for pattern in self.CHAPTER_PATTERNS:
            matches = list(pattern.finditer(text))
            all_matches.extend(matches)

        # 按位置排序
        all_matches.sort(key=lambda m: m.start())

        if not all_matches:
            return []

        chapters = []
        for i, match in enumerate(all_matches):
            title = match.group(1).strip() if match.lastindex else match.group(0).strip()
            start_pos = match.end()

            # 确定结束位置（下一个章节开始或文本末尾）
            if i + 1 < len(all_matches):
                end_pos = all_matches[i + 1].start()
            else:
                end_pos = len(text)

            # 提取章节文本
            chapter_text = text[start_pos:end_pos].strip()

            # 跳过非正文章节（简介、目录等）
            if title.lower() in self.SKIP_CHAPTER_TITLES:
                continue

            # 过滤空章节
            if chapter_text:
                chapters.append((title, chapter_text))

        return chapters

    def _create_chapter(self, chapter_id: int, title: str, text: str,
                      book_id: int, start_index: int) -> Chapter:
        """
        创建章节和chunks

        Args:
            chapter_id: 章节ID
            title: 章节标题
            text: 章节文本
            book_id: 书籍ID
            start_index: 起始索引（全局）

        Returns:
            Chapter对象
        """
        # 切分成chunks
        chunk_texts = self._split_into_chunks(text)

        chunks = []
        for chunk_id, chunk_text in enumerate(chunk_texts):
            if not chunk_text.strip():
                continue

            chunk = TextChunk(
                chunk_id=start_index + chunk_id,
                chapter_id=chapter_id,
                text=chunk_text.strip(),
                status=ChunkStatus.PENDING,
                sample_rate=22050,
                channels=1
            )
            chunks.append(chunk)

        return Chapter(
            chapter_id=chapter_id,
            title=title,
            chunks=chunks,
            start_index=start_index,
            end_index=start_index + len(chunks)
        )

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        智能文本切分

        策略：
        1. 按句子切分（标点符号）
        2. 合并句子直到接近目标大小
        3. 尊重句子边界（不在中间断开）
        4. 处理长句（超过最大大小）

        Args:
            text: 文本

        Returns:
            chunk文本列表
        """
        chunks = []
        current_chunk = ""
        current_size = 0

        # 按句子切分
        sentences = self.SENTENCE_DELIMITERS.split(text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_size = len(sentence)

            # 检查句子是否太长
            if sentence_size > self.config.max_chunk_size:
                # 强制切分长句
                sub_chunks = self._split_long_sentence(sentence)
                for sub_chunk in sub_chunks:
                    if current_chunk:
                        chunks.append(current_chunk)
                    chunks.append(sub_chunk)
                    current_chunk = ""
                    current_size = 0
                continue

            # 检查当前chunk + 新句子是否超出限制
            if current_chunk and current_size + sentence_size > self.config.max_chunk_size:
                # 保存当前chunk
                chunks.append(current_chunk)
                current_chunk = sentence
                current_size = sentence_size
            else:
                # 添加到当前chunk
                current_chunk += sentence
                current_size += sentence_size

                # 如果达到目标大小，保存chunk
                if current_size >= self.config.chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = ""
                    current_size = 0

        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        切分过长的句子

        Args:
            sentence: 长句子

        Returns:
            切分后的文本列表
        """
        # 按固定大小切分
        chunks = []
        size = self.config.chunk_size

        for i in range(0, len(sentence), size):
            chunks.append(sentence[i:i + size])

        return chunks

    def get_audio_path(self, book_id: int, chunk_id: int, model_id: str = "xiao_ya") -> str:
        """
        获取chunk的音频文件路径（包含model_id）

        Args:
            book_id: 书籍ID
            chunk_id: chunk ID
            model_id: 模型ID

        Returns:
            音频文件路径
        """
        book_dir = self.audio_dir / str(book_id)
        return str(book_dir / f"chunk_{model_id}_{chunk_id:05d}.wav")

    def ensure_audio_dir(self, book_id: int):
        """
        确保音频目录存在

        Args:
            book_id: 书籍ID
        """
        book_dir = self.audio_dir / str(book_id)
        book_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_hash(text: str, model_id: str, voice: str = "", speed: float = 1.0) -> str:
        """
        计算文本+模型的哈希值（用于缓存）

        Args:
            text: 文本内容
            model_id: 模型ID
            voice: 音色
            speed: 语速

        Returns:
            SHA256哈希值
        """
        content = f"{text}|{model_id}|{voice}|{speed}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def cleanup_audio_files(self, book_id: int, valid_chunks: List[int]):
        """
        清理无效的音频文件

        Args:
            book_id: 书籍ID
            valid_chunks: 有效的chunk ID列表
        """
        book_dir = self.audio_dir / str(book_id)
        if not book_dir.exists():
            return

        valid_set = set(valid_chunks)
        deleted = 0

        for audio_file in book_dir.glob("chunk_*.wav"):
            try:
                # 从文件名提取chunk ID
                chunk_id = int(audio_file.stem.split('_')[1])
                if chunk_id not in valid_set:
                    audio_file.unlink()
                    deleted += 1
            except (ValueError, IndexError):
                continue

        if deleted > 0:
            print(f"[ChunkManager] Cleaned up {deleted} invalid audio files")
