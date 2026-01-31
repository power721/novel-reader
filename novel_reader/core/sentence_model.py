"""
三层模型数据结构 - Sentence + TTSBatch + Playback

模拟主流安卓阅读App的架构：
- Sentence: 最小逻辑单位（UI/高亮/跳转）
- TTSBatch: 合成单位（2-4句合并）
- Playback: 连续流播放
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum, auto


class SentenceStatus(Enum):
    """句子状态"""
    PENDING = auto()      # 等待转换
    CONVERTING = auto()   # 转换中
    READY = auto()        # 已就绪
    PLAYING = auto()      # 播放中
    DONE = auto()         # 已完成


@dataclass
class Sentence:
    """
    句子 - 最小逻辑单位

    用途：
    - UI高亮
    - 用户交互（点击朗读）
    - 精确跳转（上一句/下一句）
    - 进度追踪
    """
    id: int
    text: str
    chapter_id: int

    # 状态
    status: SentenceStatus = SentenceStatus.PENDING

    # 在批次中的偏移（毫秒）
    batch_offset_ms: Optional[int] = None  # 在TTSBatch音频中的起始偏移

    # 元数据
    index_in_chapter: int = 0  # 在章节中的序号
    char_count: int = 0  # 字符数
    estimated_duration_ms: int = 0  # 预估时长

    def __post_init__(self):
        """初始化后处理"""
        self.char_count = len(self.text)
        # 估算时长：约每字50ms（可根据语速调整）
        self.estimated_duration_ms = max(1000, self.char_count * 50)


@dataclass
class TTSBatch:
    """
    TTS批次 - 合成单位

    将2-4个句子合并为一次TTS调用，减少初始化开销，
    同时保持句子级别的映射关系用于UI。
    """
    id: int
    sentences: List[Sentence] = field(default_factory=list)
    chapter_id: int = 0

    # 音频信息
    audio_path: Optional[str] = None
    duration_ms: int = 0
    status: SentenceStatus = SentenceStatus.PENDING

    # 句子映射关系
    # sentence_offsets[i] = sentences[i]在音频中的起始偏移（毫秒）
    sentence_offsets: List[int] = field(default_factory=list)

    @property
    def text(self) -> str:
        """获取批次完整文本（用于TTS）"""
        return "".join(s.text for s in self.sentences)

    @property
    def sentence_count(self) -> int:
        """句子数量"""
        return len(self.sentences)

    def get_sentence_at_offset(self, offset_ms: int) -> Optional[Sentence]:
        """
        根据时间偏移获取对应的句子

        Args:
            offset_ms: 音频偏移（毫秒）

        Returns:
            对应的Sentence，如果不在范围内返回None
        """
        for i, sent_offset in enumerate(self.sentence_offsets):
            if i + 1 < len(self.sentence_offsets):
                next_offset = self.sentence_offsets[i + 1]
                if sent_offset <= offset_ms < next_offset:
                    return self.sentences[i]
            else:
                # 最后一句
                if sent_offset <= offset_ms < self.duration_ms:
                    return self.sentences[i]
        return None


@dataclass
class ChapterV2:
    """
    章节 - 包含句子列表
    """
    id: int
    title: str
    sentences: List[Sentence] = field(default_factory=list)

    # 批次管理
    batches: List[TTSBatch] = field(default_factory=list)

    @property
    def sentence_count(self) -> int:
        """句子总数"""
        return len(self.sentences)

    @property
    def batch_count(self) -> int:
        """批次数"""
        return len(self.batches)

    def get_sentence(self, index: int) -> Optional[Sentence]:
        """获取指定索引的句子"""
        if 0 <= index < len(self.sentences):
            return self.sentences[index]
        return None


@dataclass
class BookV2:
    """
    书籍 - 包含章节列表
    """
    id: int
    title: str
    chapters: List[ChapterV2] = field(default_factory=list)

    @property
    def sentence_count(self) -> int:
        """总句子数"""
        return sum(ch.sentence_count for ch in self.chapters)

    @property
    def batch_count(self) -> int:
        """总批次数"""
        return sum(ch.batch_count for ch in self.chapters)


# ==================== 句子分割 ====================

class SentenceSplitter:
    """
    句子分割器

    将文本分割为句子，保持语义完整性
    """

    # 句子结束标记
    SENTENCE_DELIMITERS = ('。', '！', '？', '\n')

    def split_text(self, text: str) -> List[str]:
        """
        分割文本为句子

        Args:
            text: 输入文本

        Returns:
            句子列表
        """
        import re

        if not text:
            return []

        sentences = []

        # 先按标准标点分割
        pattern = f"[{''.join(re.escape(d) for d in self.SENTENCE_DELIMITERS)}]"
        parts = re.split(pattern, text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # 处理对话中的引号
            # 如果包含引号，尝试按引号分割
            if '"' in part or '"' in part:
                quoted_parts = self._split_quoted_text(part)
                sentences.extend(quoted_parts)
            else:
                sentences.append(part)

        return sentences

    def _split_quoted_text(self, text: str) -> List[str]:
        """
        分割包含引号的文本

        Args:
            text: 包含引号的文本

        Returns:
            分割后的句子列表
        """
        import re

        # 匹配引号内的内容
        pattern = r'["""](.*?)["""]'
        matches = list(re.finditer(pattern, text))

        if not matches:
            return [text]

        result = []
        last_pos = 0

        for match in matches:
            # 添加引号前的内容
            before = text[last_pos:match.start()].strip()
            if before:
                result.append(before)

            # 添加引号内容（不含引号）
            quoted = match.group(1)
            result.append(f'"{quoted}"')

            last_pos = match.end()

        # 添加最后剩余的内容
        remaining = text[last_pos:].strip()
        if remaining:
            result.append(remaining)

        return result

    def split_text_by_size(self, text: str, max_size: int = 100) -> List[str]:
        """
        按字符数限制分割，同时尊重句子边界

        Args:
            text: 输入文本
            max_size: 最大字符数

        Returns:
            句子列表
        """
        # 先按句子分割
        sentences = self.split_text(text)

        # 合并过短的句子
        result = []
        current_batch = ""
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # 如果当前句子加上会超出限制
            if current_length > 0 and current_length + sentence_length > max_size:
                result.append(current_batch)
                current_batch = sentence
                current_length = sentence_length
            else:
                # 累加到当前批次
                if current_batch:
                    current_batch += sentence
                else:
                    current_batch = sentence
                current_length += sentence_length

        # 添加最后一个批次
        if current_batch:
            result.append(current_batch)

        return result


# ==================== 批次构建器 ====================

class BatchBuilder:
    """
    批次构建器

    将句子组合为TTS批次（2-4句一批）
    """

    MIN_SENTENCES = 2  # 最少句子数
    MAX_SENTENCES = 4  # 最多句子数
    TARGET_SIZE = 150  # 目标字符数
    MAX_SIZE = 300     # 最大字符数

    def build_batches(self, sentences: List[Sentence]) -> List[TTSBatch]:
        """
        构建TTS批次

        策略：
        - 每批2-4个句子
        - 总字符数150-300左右
        - 尊重句子边界（不在句子中间分割）

        Args:
            sentences: 句子列表

        Returns:
            TTSBatch列表
        """
        if not sentences:
            return []

        batches = []
        current_batch = []
        current_size = 0
        batch_id = 0

        for sentence in sentences:
            sentence_size = len(sentence.text)

            # 检查是否应该开始新批次
            should_start_new = (
                len(current_batch) >= self.MAX_SENTENCES or  # 已达最大句子数
                (current_size > 0 and current_size + sentence_size > self.MAX_SIZE) or  # 超过最大字符数
                (len(current_batch) >= self.MIN_SENTENCES and
                 current_size + sentence_size > self.TARGET_SIZE)  # 达到目标大小
            )

            if should_start_new and current_batch:
                # 完成当前批次
                batch = TTSBatch(
                    id=batch_id,
                    sentences=current_batch.copy()
                )
                batches.append(batch)

                # 开始新批次
                batch_id += 1
                current_batch = []
                current_size = 0

            # 添加到当前批次
            current_batch.append(sentence)
            current_size += sentence_size

        # 添加最后一个批次
        if current_batch:
            batch = TTSBatch(
                id=batch_id,
                sentences=current_batch.copy()
            )
            batches.append(batch)

        return batches


# ==================== 示例 ====================

def example_usage():
    """使用示例"""

    # 1. 创建句子分割器
    splitter = SentenceSplitter()

    text = """
    这是一个阳光明媚的早晨。主人公踏上了旅程！
    前方充满了未知的挑战和机遇。

    "你疯了吗？！"他怒吼。
    """

    # 2. 分割句子
    sentences = splitter.split_text(text)

    # 创建Sentence对象
    sentence_objs = []
    for i, sent_text in enumerate(sentences):
        sent = Sentence(
            id=i,
            text=sent_text,
            chapter_id=0
        )
        sentence_objs.append(sent)

    print(f"分割出 {len(sentence_objs)} 个句子:")
    for sent in sentence_objs:
        print(f"  [{sent.id}] {sent.text[:50]}...")

    # 3. 构建批次
    builder = BatchBuilder()
    batches = builder.build_batches(sentence_objs)

    print(f"\n构建了 {len(batches)} 个批次:")
    for batch in batches:
        print(f"  批次 {batch.id}: {batch.sentence_count} 句, {len(batch.text)} 字")
        for sent in batch.sentences:
            print(f"    - {sent.text[:30]}...")

    # 4. 模拟映射关系
    print("\n句子-批次映射:")
    for sent in sentence_objs:
        print(f"  句子 {sent.id}: 批次 X, 偏移 Y ms")


if __name__ == "__main__":
    example_usage()
