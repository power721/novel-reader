#!/usr/bin/env python3
"""
创建测试 EPUB 文件
"""
import sys
from pathlib import Path

try:
    from ebooklib import epub
except ImportError:
    print("请先安装 EbookLib: pip install EbookLib")
    sys.exit(1)

def create_test_epub():
    """创建一个简单的测试 EPUB 文件"""
    
    book = epub.EpubBook()
    
    # 设置元数据
    book.set_identifier('id123456')
    book.set_title('测试小说 - 电子书导入')
    book.set_language('zh')
    book.add_author('测试作者')
    
    # 创建章节
    chapters_content = [
        ("第一章 旅程开始", """
        这是一个阳光明媚的早晨，主人公踏上了旅程。
        前方充满了未知的挑战和机遇。
        这里有很多内容，用来测试分段功能。
        这些文字会被分成多个 chunk。
        第一章节的内容比较丰富，包含了多个句子。
        主人公怀着激动的心情开始了他的冒险。
        路上遇到了各种各样的有趣事物。
        """),
        ("第二章 相遇", """
        在旅途中，他遇到了一位神秘的伙伴。
        两人决定结伴而行，共同面对困难。
        他们一起走过了许多地方。
        这段旅程充满了惊喜和意外。
        新朋友的加入让旅程更加有趣。
        """),
        ("第三章 危机", """
        突然，一场风暴席卷而来。
        他们必须团结一致，才能度过难关。
        困难重重，但他们没有放弃。
        这是一场考验意志的战斗。
        团队的力量在这一刻得到了体现。
        """),
    ]
    
    # 添加章节
    chapters = []
    toc = []
    
    for i, (title, content) in enumerate(chapters_content, 1):
        # 创建章节
        c = epub.EpubHtml(title=title, file_name=f'chap_{i}.xhtml', lang='zh')
        
        # 设置章节内容
        c.content = f'<h1>{title}</h1><p>{content}</p>'
        
        # 添加到书籍
        book.add_item(c)
        chapters.append(c)
        toc.append(c)
    
    # 设置目录
    book.toc = toc
    
    # 添加导航文件
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 设置 spine
    book.spine = ['nav'] + chapters
    
    # 写入 EPUB 文件
    output_path = Path("/tmp/test_book.epub")
    epub.write_epub(str(output_path), book, {})
    
    print(f"✓ 测试 EPUB 文件已创建: {output_path}")
    print(f"  - 书名: 测试小说 - 电子书导入")
    print(f"  - 作者: 测试作者")
    print(f"  - 章节数: {len(chapters)}")
    print(f"\n现在可以使用以下命令测试导入:")
    print(f"  python -m novel_examples.test_ebook_import")


if __name__ == "__main__":
    create_test_epub()
