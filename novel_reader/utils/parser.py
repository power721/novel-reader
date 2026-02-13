"""
文本解析模块 - 解析 TXT 文件，识别章节并分段
"""
import re
from typing import List, Tuple

# 跳过的章节标题（非正文内容）
SKIP_CHAPTER_TITLES = {
    '目录', '目次', 'table of contents', 'toc',
    '封面', '封底', '书名页', '版权页',
    '作者简介', '作者介绍', '关于作者',
    '推荐序', '推荐语', '书评',
    '附录', '后记', '跋', '编者按'
}

# EPUB 章节标记
EPUB_CHAPTER_PATTERN = re.compile(
    r'^### CHAPTER ###\s*(.+?)\s*$',
    re.MULTILINE
)

# 传统章节模式
CHAPTER_PATTERN = re.compile(
    r'^第\s*[一二三四五六七八九十百千0-9]{1,9}\s*[章节回].*?$',  # Stop at newline
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
    修复中文引号跨句问题：
    - 如果一句以左引号开头，而上一句没有以右引号结尾
    - 则把左引号并回上一句
    """
    if not sentences:
        return sentences

    fixed = [sentences[0]]

    for s in sentences[1:]:
        s = s.strip()
        if s.startswith("“") and not fixed[-1].endswith("”"):
            # 把左引号并回上一句
            fixed[-1] += "”"
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
                chunks.append(buffer.strip())
            buffer = sentence

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks


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


if __name__ == "__main__":
    # 示例：测试解析功能
    sample_text = """
第1章 雾起之日

清晨的雾气像一层薄纱笼罩着城市，街道的轮廓在灰白中若隐若现。”林舟站在阳台上，手里捧着一杯已经凉掉的咖啡。“他隐约觉得，这一天和以往不同。远处的钟声响起，低沉而缓慢，仿佛在提醒什么即将到来。
好，这里给你一份可以直接复制给 Claude Code 使用的「高质量工程型 Prompt」。
这是按 “让 Claude 产出 production 级代码，而不是示例” 来写的。

第2章 陌生来信

中午时分，一封没有署名的信被塞进了信箱。信封陈旧，边角磨损严重，像是穿越了很长时间。林舟拆开信，只看到一句话：“雾散之前，不要离开。”字迹歪斜，却透着一种不容忽视的急迫感。

第3章 旧城传闻

傍晚，他去了老城区的书店。老板是个沉默的老人，听到“雾”的时候，脸色明显变了。老人低声说，雾城每隔十年都会出现一次异常，而每一次，都会有人消失，从此再也没有回来。

第4章 夜半脚步声

夜里，林舟被一阵脚步声惊醒。那声音在走廊里回荡，缓慢而规律，却在他打开房门的一瞬间消失不见。窗外的雾比白天更浓，街灯的光被吞噬，只剩下一团模糊的亮影。

第5章 地图残片

第二天早上，他在门口发现了一张残破的地图。纸张泛黄，上面标着几个已经废弃的地名。地图角落写着一行小字：“起点在雾中，终点不在城内。”林舟意识到，自己已经被卷入其中。

第6章 同行者

在旧城的咖啡馆里，他遇到了苏晴。她似乎早就知道地图的事，并主动提出同行。苏晴说，她的哥哥十年前在雾城失踪，而这次异常，和当年的情况一模一样，她不想再失去真相。

第7章 雾中信号

两人按照地图前行，手机信号逐渐消失。就在完全失联前，屏幕闪过一行陌生坐标。雾气中传来低频的嗡鸣声，像某种装置正在运转，让人心跳不自觉地加快。

第8章 废弃车站

地图指向城外的一座废弃车站。铁轨生锈，站台空无一人，却异常干净。墙上的时钟停在十年前的同一天同一时刻。苏晴站在钟下，轻声说：“他们也许都来过这里。”

第9章 雾散时刻

随着钟声再次响起，雾气开始缓慢退去。车站深处的门缓缓打开，里面亮着微弱的白光。林舟感到一种强烈的拉扯感，仿佛只要踏进去，就再也无法回头。

第10章 城外之门

最终，他们一起走进了那扇门。光芒吞没了一切，雾城在身后彻底消失。林舟回头的瞬间，隐约看到城市恢复了平静，仿佛什么都没发生过。而他们，已经站在新的世界边缘。

""" * 100  # 重复100次以测试分段

    print("=" * 60)
    print("文本解析测试")
    print("=" * 60)

    print(split_by_sentence("清晨的雾气像一层薄纱笼罩着城市，街道的轮廓在灰白中若隐若现。”林舟站在阳台上，手里捧着一杯已经凉掉的咖啡。“他隐约觉得，这一天和以往不同。远处的钟声响起，低沉而缓慢，仿佛在提醒什么即将到来。"))

    chunks, chapters = parse_txt(sample_text, chunk_size=60)

    print(f"\n总字符数: {len(sample_text)}")
    print(f"分段数量: {len(chunks)}")
    print(f"章节数量: {len(chapters)}")

    print("\n" + "=" * 60)
    print("章节列表:")
    print("=" * 60)
    for title, chunk_idx in chapters:
        print(f"  [{chunk_idx:3d}] {title}")

    print("\n" + "=" * 60)
    print("前10个分段预览:")
    print("=" * 60)
    for i, chunk in enumerate(chunks[:10]):
        preview = chunk.replace('\n', ' ')
        print(f"\n[Chunk {i}] ({len(chunk)} 字符)")
        print(f"  {preview}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
