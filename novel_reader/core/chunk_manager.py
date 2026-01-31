"""
ChunkManager - 文本解析和Chunk管理

职责：
1. 解析文本文件
2. 识别章节
3. 切分成chunk
4. 管理chunk的生命周期
"""
import re
from pathlib import Path
from typing import List, Tuple, Optional
import hashlib

from .models import TextChunk, Chapter, Book, ChunkStatus, AUDIOBOOK_CONFIG


class ChunkManager:
    """Chunk管理器 - 文本解析和切分"""

    # 章节标题正则（中文）
    CHAPTER_PATTERN = re.compile(
        r'^(第[一二三四五六七八九十百千零\d]+[章节回卷集部篇].*)$',
        re.MULTILINE
    )

    # 句子切分正则（按标点符号）
    SENTENCE_PATTERN = re.compile(r'([。！？；\n])')

    def __init__(self, config: dict = None):
        """
        初始化ChunkManager

        Args:
            config: 配置字典，默认使用AUDIOBOOK_CONFIG
        """
        self.config = config or AUDIOBOOK_CONFIG
        self.chunk_size = self.config.get("text_chunk_size", 100)

    def parse_book(self, file_path: str, book_id: int) -> Book:
        """
        解析书籍文件

        Args:
            file_path: 文本文件路径
            book_id: 书籍ID

        Returns:
            Book对象
        """
        # 读取文本
        text = self._load_text(file_path)
        title = Path(file_path).stem

        # 识别章节
        chapters_text = self._split_chapters(text)

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
            chapters.append(chapter)
            current_index += len(chapter.chunks)

        return Book(
            book_id=book_id,
            title=title,
            chapters=chapters,
            file_path=file_path,
            current_chunk_index=0
        )

    def _load_text(self, file_path: str) -> str:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _split_chapters(self, text: str) -> List[Tuple[str, str]]:
        """
        按章节标题切分文本

        Returns:
            [(章节标题, 章节文本), ...]
        """
        # 查找所有章节标题位置
        matches = list(self.CHAPTER_PATTERN.finditer(text))

        if not matches:
            # 没有章节，整个作为一章
            return [("正文", text)]

        chapters = []
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start_pos = match.start()

            # 确定结束位置
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            chapter_text = text[start_pos:end_pos].strip()
            # 移除标题行
            chapter_text = chapter_text.split('\n', 1)[1] if '\n' in chapter_text else chapter_text

            if chapter_text:  # 跳过空章节
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
            chunk = TextChunk(
                chunk_id=start_index + chunk_id,
                chapter_id=chapter_id,
                text=chunk_text.strip(),
                status=ChunkStatus.PENDING
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
        将文本切分成chunks

        策略：
        1. 按句子切分
        2. 合并句子直到接近目标大小
        3. 避免在句子中间断开

        Args:
            text: 文本

        Returns:
            chunk文本列表
        """
        # 按句子切分
        sentences = self.SENTENCE_PATTERN.split(text)

        # 合并成chunks
        chunks = []
        current_chunk = ""
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_size = len(sentence)

            # 如果当前chunk + 新句子超出太多，先保存当前chunk
            if current_chunk and current_size + sentence_size > self.chunk_size * 1.5:
                chunks.append(current_chunk)
                current_chunk = sentence
                current_size = sentence_size
            else:
                current_chunk += sentence
                current_size += sentence_size

                # 如果接近目标大小，保存chunk
                if current_size >= self.chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = ""
                    current_size = 0

        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_audio_path(self, book_id: int, chunk_id: int) -> str:
        """获取chunk的音频文件路径"""
        from pathlib import Path
        audio_dir = Path("data/audio") / str(book_id)
        return str(audio_dir / f"chunk_{chunk_id:05d}.wav")

    @staticmethod
    def calculate_hash(text: str, model_path: str, voice: str = "") -> str:
        """
        计算文本+模型的哈希值（用于缓存）

        Args:
            text: 文本内容
            model_path: 模型路径
            voice: 音色

        Returns:
            SHA1哈希值
        """
        content = f"{text}|{model_path}|{voice}"
        return hashlib.sha1(content.encode('utf-8')).hexdigest()
