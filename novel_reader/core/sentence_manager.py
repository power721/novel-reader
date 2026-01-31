"""
句子管理器 - 基于三层模型的文本解析和管理

实现主流安卓阅读App的架构：
- Sentence: 最小逻辑单位
- TTSBatch: 合成单位（2-4句）
- 播放时连续流但保持句子级映射
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict
import hashlib

from .sentence_model import (
    Sentence,
    SentenceStatus,
    TTSBatch,
    ChapterV2,
    BookV2,
    SentenceSplitter,
    BatchBuilder
)
from .audio_cache import AudioCache


class SentenceManager:
    """
    句子管理器

    职责：
    - 文本分割（句子级）
    - 批次构建（2-4句一批）
    - TTS任务调度
    - 音频缓存管理
    """

    def __init__(self, batch_size: int = 150):
        """
        初始化句子管理器

        Args:
            batch_size: 目标批次大小（字符数）
        """
        self.splitter = SentenceSplitter()
        self.batch_builder = BatchBuilder()

        # 存储书籍数据
        self.books: Dict[int, BookV2] = {}
        self.current_book_id: Optional[int] = None

    def parse_book(self, file_path: str, book_id: int) -> BookV2:
        """
        解析书籍为三层模型

        Args:
            file_path: TXT文件路径
            book_id: 书籍ID

        Returns:
            BookV2对象
        """
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # 获取书名
        title = Path(file_path).stem

        # 分割章节（简单按"第X章"分割）
        chapter_texts = self._split_chapters(text)

        # 创建章节数据
        chapters = []
        global_sentence_id = 0

        for chapter_idx, chapter_text in enumerate(chapter_texts):
            # 分割句子
            sentence_texts = self.splitter.split_text(chapter_text)

            # 创建Sentence对象
            sentences = []
            for sent_idx, sent_text in enumerate(sentence_texts):
                sentence = Sentence(
                    id=global_sentence_id,
                    text=sent_text,
                    chapter_id=chapter_idx,
                    index_in_chapter=sent_idx
                )
                sentences.append(sentence)
                global_sentence_id += 1

            # 构建批次
            batches = self.batch_builder.build_batches(sentences)

            # 创建ChapterV2
            chapter = ChapterV2(
                id=chapter_idx,
                title=f"第{chapter_idx + 1}章",  # 可以改进标题识别
                sentences=sentences,
                batches=batches
            )
            chapters.append(chapter)

        # 创建BookV2
        book = BookV2(
            id=book_id,
            title=title,
            chapters=chapters
        )

        # 缓存
        self.books[book_id] = book
        self.current_book_id = book_id

        return book

    def _split_chapters(self, text: str) -> List[str]:
        """
        简单的章节分割

        Args:
            text: 完整文本

        Returns:
            章节文本列表
        """
        import re

        # 匹配"第X章"或"第X节"
        pattern = r'第[一二三四五六七八九十百零\d]+[章回节]'

        # 找到所有章节标题的位置
        matches = list(re.finditer(pattern, text))

        if not matches:
            # 没有章节，整体作为一章
            return [text]

        # 分割章节
        chapters = []
        last_pos = 0

        for match in matches:
            # 添加上一章
            if last_pos < match.start():
                chapter_text = text[last_pos:match.start()].strip()
                if chapter_text:
                    chapters.append(chapter_text)
            last_pos = match.start()

        # 添加最后一章
        if last_pos < len(text):
            chapter_text = text[last_pos:].strip()
            if chapter_text:
                chapters.append(chapter_text)

        return chapters

    def get_sentence(self, sentence_id: int) -> Optional[Sentence]:
        """
        获取指定句子

        Args:
            sentence_id: 句子ID

        Returns:
            Sentence对象或None
        """
        if self.current_book_id not in self.books:
            return None

        book = self.books[self.current_book_id]

        # 遍历章节查找句子
        for chapter in book.chapters:
            sentence = chapter.get_sentence(sentence_id)
            if sentence:
                return sentence

        return None

    def get_next_sentence(self, current_sentence_id: int) -> Optional[Sentence]:
        """
        获取下一句

        Args:
            current_sentence_id: 当前句子ID

        Returns:
            下一句或None
        """
        if self.current_book_id not in self.books:
            return None

        book = self.books[self.current_book_id]

        # 扁平查找
        all_sentences = []
        for chapter in book.chapters:
            all_sentences.extend(chapter.sentences)

        # 找到当前句子的位置
        for i, sent in enumerate(all_sentences):
            if sent.id == current_sentence_id:
                if i + 1 < len(all_sentences):
                    return all_sentences[i + 1]
                return None

        return None

    def get_prev_sentence(self, current_sentence_id: int) -> Optional[Sentence]:
        """
        获取上一句

        Args:
            current_sentence_id: 当前句子ID

        Returns:
            上一句或None
        """
        if self.current_book_id not in self.books:
            return None

        book = self.books[self.current_book_id]

        # 扁平查找
        all_sentences = []
        for chapter in book.chapters:
            all_sentences.extend(chapter.sentences)

        # 找到当前句子的位置
        for i, sent in enumerate(all_sentences):
            if sent.id == current_sentence_id:
                if i > 0:
                    return all_sentences[i - 1]
                return None

        return None

    def get_batch(self, batch_id: int) -> Optional[TTSBatch]:
        """
        获取指定批次

        Args:
            batch_id: 批次ID

        Returns:
            TTSBatch对象或None
        """
        if self.current_book_id not in self.books:
            return None

        book = self.books[self.current_book_id]

        # 遍历章节查找批次
        for chapter in book.chapters:
            for batch in chapter.batches:
                if batch.id == batch_id:
                    return batch

        return None

    def get_current_book(self) -> Optional[BookV2]:
        """获取当前书籍"""
        if self.current_book_id is not None:
            return self.books.get(self.current_book_id)
        return None

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        if self.current_book_id not in self.books:
            return {}

        book = self.books[self.current_book_id]

        # 统计批次大小分布
        batch_sizes = []
        for chapter in book.chapters:
            for batch in chapter.batches:
                batch_sizes.append(len(batch.text))

        return {
            "sentence_count": book.sentence_count,
            "batch_count": book.batch_count,
            "chapter_count": len(book.chapters),
            "avg_batch_size": sum(batch_sizes) / len(batch_sizes) if batch_sizes else 0,
            "min_batch_size": min(batch_sizes) if batch_sizes else 0,
            "max_batch_size": max(batch_sizes) if batch_sizes else 0,
        }


# ==================== 缓存键生成 ====================

def get_batch_cache_key(batch: TTSBatch, model: str, voice: str, speed: float) -> str:
    """
    生成批次的缓存键

    Args:
        batch: TTSBatch对象
        model: TTS模型
        voice: 音色
        speed: 语速

    Returns:
        缓存键
    """
    # 将批次文本拼接
    content = batch.text + model + voice + str(speed)
    # 使用SHA256哈希
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


# ==================== 示例 ====================

def example_usage():
    """使用示例"""

    # 1. 创建测试文本
    test_text = """
第一章 旅程开始

这是一个阳光明媚的早晨。主人公踏上了旅程！
前方充满了未知的挑战和机遇。

"你疯了吗？！"他怒吼。
两人对视着，气氛紧张。

第二章相遇

在旅途中，他遇到了一位神秘的伙伴。
两人决定结伴而行，共同面对困难。
""".strip()

    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_text)
        temp_path = f.name

    try:
        # 2. 创建管理器
        manager = SentenceManager()

        # 3. 解析书籍
        book = manager.parse_book(temp_path, book_id=1)

        print("=" * 60)
        print("书籍解析结果")
        print("=" * 60)
        print(f"\n书名: {book.title}")
        print(f"章节数: {len(book.chapters)}")
        print(f"总句子数: {book.sentence_count}")
        print(f"总批次数: {book.batch_count}")

        # 4. 显示章节详情
        for chapter in book.chapters:
            print(f"\n{chapter.title}:")
            print(f"  句子数: {chapter.sentence_count}")
            print(f"  批次数: {chapter.batch_count}")

            # 显示批次详情
            for batch in chapter.batches[:3]:  # 只显示前3个批次
                print(f"    批次 {batch.id}: {batch.sentence_count} 句, {len(batch.text)} 字")

        # 5. 显示句子示例
        print("\n" + "=" * 60)
        print("句子示例（前5句）")
        print("=" * 60)

        sentence_count = 0
        for chapter in book.chapters:
            for sentence in chapter.sentences:
                if sentence_count >= 5:
                    break
                print(f"\n[{sentence.id}] {sentence.text}")
                sentence_count += 1

        # 6. 显示统计信息
        print("\n" + "=" * 60)
        print("统计信息")
        print("=" * 60)

        stats = manager.get_statistics()
        print(f"平均批次大小: {stats['avg_batch_size']:.1f} 字")
        print(f"最小批次大小: {stats['min_batch_size']} 字")
        print(f"最大批次大小: {stats['max_batch_size']} 字")

        # 7. 测试句子导航
        print("\n" + "=" * 60)
        print("句子导航测试")
        print("=" * 60)

        if book.sentence_count > 0:
            # 获取第一句
            first_sentence = book.chapters[0].sentences[0]
            print(f"\n第一句: [{first_sentence.id}] {first_sentence.text}")

            # 获取下一句
            next_sentence = manager.get_next_sentence(first_sentence.id)
            if next_sentence:
                print(f"下一句: [{next_sentence.id}] {next_sentence.text}")

            # 获取上一句（应该是None）
            prev_sentence = manager.get_prev_sentence(first_sentence.id)
            print(f"上一句: {prev_sentence if prev_sentence else 'None'}")

        print("\n✅ 句子管理器测试完成！")

    finally:
        # 清理临时文件
        Path(temp_path).unlink()


if __name__ == "__main__":
    example_usage()
