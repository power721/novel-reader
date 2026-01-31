#!/usr/bin/env python3
"""
文本解析模块使用示例
"""
from novel_reader.utils import parse_txt, load_txt_file


# 示例 1: 解析字符串
sample_text = """
第一章 旅程开始

这是一个阳光明媚的早晨，主人公踏上了旅程。
前方充满了未知的挑战和机遇。

第二章 相遇

在旅途中，他遇到了一位神秘的伙伴。
两人决定结伴而行，共同面对困难。

第三章 危机

突然，一场风暴席卷而来。
他们必须团结一致，才能度过难关。

第四章 胜利

经过不懈的努力，他们终于战胜了困难。
这段旅程让他们成长了许多。

全文完。
"""

print("=" * 60)
print("示例 1: 解析文本字符串")
print("=" * 60)

chunks, chapters = parse_txt(sample_text, chunk_size=200)

print(f"\n✓ 总字符数: {len(sample_text)}")
print(f"✓ 分段数量: {len(chunks)}")
print(f"✓ 章节数量: {len(chapters)}")

print("\n章节列表:")
for title, chunk_idx in chapters:
    print(f"  {chunk_idx:2d} → {title}")

print("\n" + "=" * 60)
print("示例 2: 从文件读取并解析")
print("=" * 60)

# 创建一个测试 TXT 文件
test_file = "/tmp/test_novel.txt"
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(sample_text)

print(f"\n已创建测试文件: {test_file}")

# 从文件加载并解析
text = load_txt_file(test_file)
chunks, chapters = parse_txt(text, chunk_size=200)

print(f"✓ 读取字符数: {len(text)}")
print(f"✓ 分段数量: {len(chunks)}")
print(f"✓ 章节数量: {len(chapters)}")

print("\n" + "=" * 60)
print("使用方法总结")
print("=" * 60)
print("""
from novel_reader.utils import parse_txt, load_txt_file

# 方法 1: 解析字符串
text = "你的小说内容..."
chunks, chapters = parse_txt(text, chunk_size=800)

# 方法 2: 从文件读取
text = load_txt_file("path/to/novel.txt")
chunks, chapters = parse_txt(text, chunk_size=800)

# 返回值:
# - chunks: List[str]        # 文本分段列表
# - chapters: List[Tuple]    # [(章节标题, 起始chunk索引), ...]
""")
