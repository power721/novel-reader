"""
电子书格式转换模块 - 支持 EPUB 和 MOBI 转 TXT
"""
from pathlib import Path
from typing import Tuple, Optional
import shutil

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
    
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        html_content = item.get_content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        text_lines = []
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div']):
            text = element.get_text(strip=True)
            if text:
                text_lines.append(text)
        
        chapter_text = '\n\n'.join(text_lines)
        
        if chapter_text:
            all_text_parts.append(chapter_text)
    
    full_text = '\n\n'.join(all_text_parts)
    
    return full_text, title


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
