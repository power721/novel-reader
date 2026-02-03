"""
电子书格式转换模块 - 支持 EPUB 和 MOBI 转 TXT
"""
from pathlib import Path
from typing import Tuple, Optional, List
import shutil

# EPUB 章节标记
CHAPTER_MARKER = "### CHAPTER ###"

try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = None

try:
    import mobi
except ImportError:
    mobi = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def get_file_format(file_path: Path | str) -> str:
    """获取文件格式"""
    file_path = Path(file_path)
    return file_path.suffix.lower().lstrip('.')


def is_ebook_file(file_path: str) -> bool:
    """检查是否是支持的电子书格式"""
    supported_extensions = {'.epub', '.mobi', '.azw3', '.azw'}
    return Path(file_path).suffix.lower() in supported_extensions


def extract_epub_text(epub_path: Path) -> Tuple[str, str]:
    """
    从 EPUB 文件提取文本和书名
    
    Args:
        epub_path: EPUB 文件路径
        
    Returns:
        (完整文本, 书名)
    """
    if ebooklib is None:
        raise ImportError("请安装 EbookLib: pip install EbookLib")
    
    if BeautifulSoup is None:
        raise ImportError("请安装 BeautifulSoup4: pip install beautifulsoup4")
    
    book = epub.read_epub(str(epub_path))
    
    title_metadata = book.get_metadata('DC', 'title')
    if title_metadata:
        title = title_metadata[0][0]
    else:
        title = epub_path.stem
    
    all_text_parts = []
    
    # 获取 TOC（目录）
    toc = book.toc or []
    
    # 获取所有文档项的映射
    items_map = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        items_map[item.get_name()] = item
    
    # 创建章节标题映射（文件名 -> 章节标题）
    chapter_titles = {}
    
    # 如果有 TOC，提取章节标题
    if toc:
        for item in toc:
            if hasattr(item, 'href'):
                href = item.href
                file_name = href.split('#')[0]
                title_text = getattr(item, 'title', '')
                if title_text:
                    chapter_titles[file_name] = title_text
    
    # 按 spine 顺序或文件名顺序提取所有章节
    # 优先使用 spine 顺序，因为这是作者定义的阅读顺序
    spine = book.spine or []
    processed_files = set()
    
    # 按 spine 顺序处理
    if spine:
        for item in spine:
            if isinstance(item, str):
                # spine 中是文件名
                if item in items_map and item not in processed_files:
                    doc_item = items_map[item]
                    chapter_text = _extract_text_from_html(doc_item.get_content())
                    
                if chapter_text:
                    # 获取章节标题（优先使用 TOC 标题，其次使用 HTML 标题）
                    chapter_title = chapter_titles.get(item, '')
                    if not chapter_title:
                        chapter_title = _extract_title_from_html(doc_item.get_content())
                    
                    # 如果还是没有标题，使用文件名
                    if not chapter_title:
                        chapter_title = Path(item).stem
                    
                    # 使用特殊标记章节标题
                    all_text_parts.append(f"{CHAPTER_MARKER} {chapter_title}")
                    all_text_parts.append(chapter_text)
                    processed_files.add(item)
    
    # 处理 spine 中没有的文件
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        file_name = item.get_name()
        if file_name not in processed_files:
            chapter_text = _extract_text_from_html(item.get_content())
            
            if chapter_text:
                chapter_title = chapter_titles.get(file_name, '')
                if not chapter_title:
                    chapter_title = _extract_title_from_html(item.get_content())
                
                if not chapter_title:
                    chapter_title = Path(file_name).stem
                
                # 使用特殊标记章节标题
                all_text_parts.append(f"{CHAPTER_MARKER} {chapter_title}")
                all_text_parts.append(chapter_text)
    
    full_text = '\n\n'.join(all_text_parts)
    
    return full_text, title


def _extract_text_from_html(html_content: bytes) -> str:
    """
    从 HTML 内容中提取纯文本
    
    Args:
        html_content: HTML 字节内容
        
    Returns:
        提取的文本
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    text_lines = []
    
    # 获取所有段落和 div 内容
    for element in soup.find_all(['p', 'div']):
        # 跳过标题元素
        if element.name in ['h1', 'h2', 'h3']:
            continue
        
        text = element.get_text(strip=True)
        if text and len(text) > 2:  # 过滤过短的文本
            text_lines.append(text)
    
    return '\n\n'.join(text_lines)


def _extract_title_from_html(html_content: bytes) -> str:
    """
    从 HTML 内容中提取标题（h1/h2/h3）
    
    Args:
        html_content: HTML 字节内容
        
    Returns:
        提取的标题
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找第一个标题元素
    title_elem = soup.find(['h1', 'h2', 'h3'])
    if title_elem:
        return title_elem.get_text(strip=True)
    
    return ''


def extract_mobi_text(mobi_path: Path) -> Tuple[str, str]:
    """
    从 MOBI 文件提取文本和书名
    
    Args:
        mobi_path: MOBI 文件路径
        
    Returns:
        (完整文本, 书名)
    """
    if mobi is None:
        raise ImportError("请安装 mobi 库: pip install mobi")
    
    if BeautifulSoup is None:
        raise ImportError("请安装 BeautifulSoup4: pip install beautifulsoup4")
    
    tempdir, extracted_file = mobi.extract(str(mobi_path))
    
    try:
        extracted_path = Path(extracted_file)
        title = mobi_path.stem
        
        if extracted_path.suffix == '.epub':
            text, epub_title = extract_epub_text(extracted_path)
            if epub_title and epub_title != extracted_path.stem:
                title = epub_title
            return text, title
            
        elif extracted_path.suffix == '.html':
            with open(extracted_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()
            
            return text, title
            
        elif extracted_path.suffix == '.pdf':
            raise ValueError("MOBI Print Replica PDF 格式暂不支持")
            
        else:
            raise ValueError(f"未知的 MOBI 提取格式: {extracted_path.suffix}")
            
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def convert_ebook_to_txt(
    ebook_path: str, 
    output_dir: Optional[Path | str] = None
) -> Tuple[str, str]:
    """
    将电子书转换为 TXT 文件
    
    Args:
        ebook_path: 电子书文件路径
        output_dir: 输出目录（默认使用临时目录）
        
    Returns:
        (txt_file_path, book_title)
    """
    ebook_path = Path(ebook_path)
    
    if not ebook_path.exists():
        raise FileNotFoundError(f"文件不存在: {ebook_path}")
    
    file_format = get_file_format(ebook_path)
    
    if file_format == 'epub':
        text, book_title = extract_epub_text(ebook_path)
    elif file_format in {'mobi', 'azw3', 'azw'}:
        text, book_title = extract_mobi_text(ebook_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_format}")
    
    if output_dir is None:
        output_dir = Path("data/converted")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    txt_filename = f"{ebook_path.stem}.txt"
    txt_path = output_dir / txt_filename
    
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return str(txt_path), book_title
