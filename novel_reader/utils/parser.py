"""
文本解析模块 - 解析 TXT 文件，识别章节并分段
"""
import re
import os
from typing import List, Tuple, Dict, Optional

# 内存缓存：{book_id: (chunks, chapters, mtime)}
_parse_cache: Dict[int, Tuple[List[str], List[Tuple[str, int]], float]] = {}


# 跳过的章节标题（非正文内容）
SKIP_CHAPTER_TITLES = {
    '目录', '目次', 'table of contents', 'toc',
    '封面', '封底', '书名页', '版权页',
    '作者简介', '作者介绍', '关于作者',
    '推荐序', '推荐语', '书评',
    '附录', '后记', '跋', '编者按',
    '制作说明', '版权信息', '书籍信息', '声明'
}

# EPUB 章节标记
EPUB_CHAPTER_PATTERN = re.compile(
    r'^### CHAPTER ###\s*(.+?)\s*$',
    re.MULTILINE
)

# 传统章节模式（支持：章、节、卷、回）
CHAPTER_PATTERN = re.compile(
    r'^\s*(☆、)?第\s*[一二三四五六七八九十百千0-9]{1,9}\s*[章节卷回].*?$',
    re.MULTILINE
)

SENTENCE_SEP = re.compile(
    r'([。！？]+(?:[”’」』】"\n]+)?)'
)
CLAUSE_SEP = re.compile(r'([，、；])')


def normalize_text(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def split_by_sentence(text: str) -> List[str]:
    parts = SENTENCE_SEP.split(text)
    sentences = []
    buf = ""

    for part in parts:
        buf += part
        if SENTENCE_SEP.match(part):
            sentences.append(buf.strip())
            buf = ""

    if buf.strip():
        sentences.append(buf.strip())

    # ✅ 修复中文引号跨句
    sentences = fix_quote_boundary(sentences)

    return sentences


def fix_quote_boundary(sentences: List[str]) -> List[str]:
    """
    修复引号跨句问题：
    - 如果一句以左引号开头，而上一句没有以右引号结尾
    - 则把左引号并回上一句
    """
    if not sentences:
        return sentences

    fixed = [sentences[0]]

    for s in sentences[1:]:
        s = s.strip()
        # Check both Chinese and English quotes
        starts_with_quote = s.startswith('”') or s.startswith('"')
        text = fixed[-1]
        count = (
                text.count('“') +
                text.count('”') +
                text.count('"')
        )
        pair_with_quote = count % 2 == 0

        if starts_with_quote and not pair_with_quote:
            # 把左引号并回上一句
            quote_char = s[0]  # Get the actual quote character used
            fixed[-1] += quote_char
            fixed.append(s[1:].lstrip())
        else:
            fixed.append(s)

    return fixed


def smart_split_chunks(text: str, chunk_size: int) -> List[str]:
    """
    人声友好的 chunk 切分
    """
    chunks: List[str] = []
    buffer = ""

    for sentence in split_by_sentence(text):
        if len(buffer) + len(sentence) <= chunk_size:
            buffer += sentence
        else:
            if buffer.strip():
                chunk_text = buffer.strip()
                # 跳过只包含省略号或没有有意义内容的分段
                if not _is_meaningless_chunk(chunk_text):
                    chunks.append(chunk_text)
            buffer = sentence

    if buffer.strip():
        chunk_text = buffer.strip()
        # 跳过只包含省略号或没有有意义内容的分段
        if not _is_meaningless_chunk(chunk_text):
            chunks.append(chunk_text)

    return chunks


def _is_meaningless_chunk(text: str) -> bool:
    """
    判断分段是否没有有意义的内容，应该被跳过

    Args:
        text: 分段文本

    Returns:
        True 如果分段应该被跳过，否则 False
    """
    stripped = text.strip()

    # 跳过只有省略号的分段
    if stripped == "...":
        return True

    # 跳过只有省略号（中英文）的分段
    if stripped in ("...", "…", "。。。", "‥‥", "....", "....."):
        return True

    # 跳过纯空白分段
    if not stripped:
        return True

    return False


def parse_txt(
        text: str,
        chunk_size: int = 60
) -> Tuple[List[str], List[Tuple[str, int]]]:
    text = normalize_text(text)

    # === 优先检查 EPUB 章节标记 ===
    epub_matches = list(EPUB_CHAPTER_PATTERN.finditer(text))

    # === 如果没有 EPUB 标记，检查传统章节 ===
    chapter_matches = list(CHAPTER_PATTERN.finditer(text))

    # 确定使用哪种章节识别
    matches = epub_matches if epub_matches else chapter_matches

    # === 没有章节 ===
    if not matches:
        chunks = smart_split_chunks(text, chunk_size)
        return chunks, [("全文", 0)]

    chunks: List[str] = []
    chapters: List[Tuple[str, int]] = []

    for idx, match in enumerate(matches):
        if epub_matches:
            # EPUB 标记格式：### CHAPTER ### 章节标题
            title = match.group(1).strip()
        else:
            # 传统格式：第一章 xxx
            title = match.group().strip()

        # 跳过非正文章节（简介、目录等）
        if title.lower() in SKIP_CHAPTER_TITLES:
            continue

        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)

        chapter_start_chunk = len(chunks)

        # ① 章节标题单独成 chunk
        chunks.append(title)
        body = text[match.end():end].strip()

        # ② 正文再切
        body_chunks = smart_split_chunks(body, chunk_size)

        chunks.extend(body_chunks)
        chapters.append((title, chapter_start_chunk))

    return chunks, chapters


def load_txt_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_txt_cached(book_id: int, book: dict) -> Tuple[List[str], List[Tuple[str, int]]]:
    """
    带内存缓存的文本解析

    Args:
        book_id: 书籍 ID
        book: 书籍信息字典（必须提供）

    Returns:
        (chunks, chapters) - 分段列表和章节信息
    """
    file_path = book['file_path']

    # 获取文件修改时间
    mtime = os.path.getmtime(file_path)

    # 检查缓存
    if book_id in _parse_cache:
        chunks, chapters, cached_mtime = _parse_cache[book_id]
        if cached_mtime == mtime:
            # 缓存命中
            return chunks, chapters

    # 缓存未命中或文件已修改，重新解析
    text = load_txt_file(file_path)
    chunks, chapters = parse_txt(text)

    # 更新缓存
    _parse_cache[book_id] = (chunks, chapters, mtime)

    return chunks, chapters


def clear_parse_cache(book_id: Optional[int] = None) -> None:
    """
    清理解析缓存

    Args:
        book_id: 指定书籍 ID，则只清除该书籍的缓存；否则清除全部缓存
    """
    if book_id:
        _parse_cache.pop(book_id, None)
    else:
        _parse_cache.clear()


def parse_txt_preserve_format(
        file_path: str
) -> Tuple[List[str], List[Tuple[str, int]]]:
    """
    保留原始文本格式的解析方法

    完全保留段落结构和换行符，不进行句子级别的分割

    Args:
        file_path: 文本文件路径

    Returns:
        (chapter_texts, chapter_info) - 章节文本列表和章节信息
    """
    # 读取原始文件内容
    text = load_txt_file(file_path)
    if not text:
        return [], []

    # 使用现有的章节识别逻辑
    epub_matches = list(EPUB_CHAPTER_PATTERN.finditer(text))
    chapter_matches = list(CHAPTER_PATTERN.finditer(text))

    # 确定使用哪种章节识别
    matches = epub_matches if epub_matches else chapter_matches

    if not matches:
        # 没有章节，整本书作为一个章节
        return [text], [(os.path.basename(file_path), 0)]

    chapter_texts: List[str] = []
    chapter_info: List[Tuple[str, int]] = []

    # 遍历所有章节
    for idx, match in enumerate(matches):
        if epub_matches:
            # EPUB 标记格式：### CHAPTER ### 章节标题
            title = match.group(1).strip()
        else:
            # 传统格式：第一章 xxx
            title = match.group().strip()

        # 跳过非正文章节
        if title.lower() in SKIP_CHAPTER_TITLES:
            continue

        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)

        # 提取章节完整内容
        # EPUB 标记：从 match.end() 开始（跳过 ### CHAPTER ### 标记行）
        # 传统格式：从 start 开始（包含章节标题）
        content_start = match.end() if epub_matches else start
        chapter_text = text[content_start:end].strip()

        # 保存章节信息
        chapter_info.append((title, len(chapter_texts)))
        # 保存章节文本（包含标题）
        chapter_texts.append(chapter_text)

    return chapter_texts, chapter_info


if __name__ == "__main__":
    # 示例：测试解析功能
    sample_text = """
第一章 旅程开始

    清晨的雾气像一层薄纱笼罩着城市，街道的轮廓在灰白中若隐若现。"林舟站在阳台上，手里捧着一杯已经凉掉的咖啡。」

    第二章 相遇

    在旅途中，他遇到了一位神秘的伙伴。两人决定结伴而行，共同面对困难。

    第三章 夜半脚步声

    夜里，他去了老城区的书店。老板是个沉默的老人，听到"雾"的时候，脸色明显变了。老人低声说，雾城每隔十年都会出现一次异常，而每一次，都会有人消失，从此再也没有回来。

    """ * 1  # 重复50次以获得更多内容

    print("=" * 60)
    print("文本解析测试")
    print("=" * 60)

    print("原始文本：")
    print(sample_text)
    print()

    # 测试parse_txt_preserve_format() 需要真实的文件路径
    # 首先创建测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
        f.write(sample_text)
        temp_path = f.name

    chapter_texts, chapter_info = parse_txt_preserve_format(temp_path)

    print(f"总字符数: {len(sample_text)}")
    print(f"章节数: {len(chapter_info)}")
    print()

    print("章节信息：")
    print("-" * 60)
    for i, (title, start) in enumerate(chapter_info):
        print(f"  第 {i+1} 章: {title}")
        print(f"  起始chunk: {start}")

    print()
    print("前3个章节的换行符检查：")
    print("=" * 60)

    for i, (text, (title, start)) in enumerate(chapter_texts[:3]):
        newline_count = text.count('\n')
        print(f"  第 {i+1} 章 ({title})")
        print(f"  字符数: {len(text)}")
        print(f"  换行符数: {newline_count}")
        print(f"  状态: {'✓ 保留' if newline_count > 0 else '✗ 丢失'} 换行符")

    print("=" * 60)
    print("测试完成！")
