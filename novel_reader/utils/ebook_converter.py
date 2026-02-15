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

    # 跳过的导航文件名模式
    skip_patterns = ('nav', 'toc', 'ncx', 'cover', 'title')

    # 按 spine 顺序处理
    if spine:
        for item in spine:
            # spine 中的项可能是字符串（文件名）或元组（ID, linear）
            if isinstance(item, tuple):
                spine_id = item[0]
                # 使用 get_item_with_id() 获取实际的文档项
                doc_item = book.get_item_with_id(spine_id)
            elif isinstance(item, str):
                # 直接是文件名
                doc_item = items_map.get(item)
            else:
                continue

            if not doc_item:
                continue

            file_name = doc_item.get_name()

            # 跳过导航和目录文件
            if any(pattern in file_name.lower() for pattern in skip_patterns):
                continue

            if file_name in processed_files:
                continue

            chapter_text = _extract_text_from_html(doc_item.get_content())

            # 获取章节标题（优先使用 TOC 标题，其次使用 HTML 标题）
            chapter_title = chapter_titles.get(file_name, '')
            if not chapter_title:
                chapter_title = _extract_title_from_html(doc_item.get_content())

            # 如果还是没有标题，使用文件名
            if not chapter_title:
                chapter_title = Path(file_name).stem

            # 如果有内容或者至少有标题，都视为有效章节
            if chapter_text or chapter_title:
                # 跳过书名作为章节标题
                if chapter_title == title:
                    all_text_parts.append(chapter_text)
                    processed_files.add(file_name)
                    continue

                # 使用特殊标记章节标题
                all_text_parts.append(f"{CHAPTER_MARKER} {chapter_title}")
                all_text_parts.append(chapter_text)
                processed_files.add(file_name)

    # 处理 spine 中没有的文件
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        file_name = item.get_name()

        # 跳过导航和目录文件
        if any(pattern in file_name.lower() for pattern in skip_patterns):
            continue

        if file_name not in processed_files:
            chapter_text = _extract_text_from_html(item.get_content())

            # 获取章节标题（优先使用 TOC 标题，其次使用 HTML 标题）
            chapter_title = chapter_titles.get(file_name, '')
            if not chapter_title:
                chapter_title = _extract_title_from_html(item.get_content())

            # 如果还是没有标题，使用文件名
            if not chapter_title:
                chapter_title = Path(file_name).stem

            # 如果有内容或者至少有标题，都视为有效章节
            if chapter_text or chapter_title:
                # 跳过书名作为章节标题
                if chapter_title == title:
                    all_text_parts.append(chapter_text)
                    continue

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

    # 移除脚本和样式
    for script in soup(['script', 'style']):
        script.decompose()

    # 移除标题元素（h1-h6），因为章节标题单独处理
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        h.decompose()

    # 获取所有文本，用换行符分隔
    text = soup.get_text(separator='\n', strip=True)

    # 清理多余的空行
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n\n'.join(lines)


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


def _extract_mobi_toc_from_ncx(ncx_path: Path, html_bytes: bytes) -> List[Tuple[int, int, str]]:
    """
    从 NCX 文件提取目录信息，并根据HTML文件调整位置
    
    Args:
        ncx_path: NCX 文件路径
        html_bytes: HTML文件字节内容
        
    Returns:
        [(锚点位置, 实际内容位置, 章节标题)] 列表
    """
    if not ncx_path.exists():
        return []

    try:
        with open(ncx_path, 'r', encoding='utf-8') as f:
            ncx_content = f.read()

        soup = BeautifulSoup(ncx_content, 'xml')

        nav_points = soup.find_all('navPoint')
        toc_data = []

        for nav_point in nav_points:
            nav_label = nav_point.find('text')
            nav_content = nav_point.find('content')

            if nav_label and nav_content:
                label = nav_label.get_text(strip=True)
                src = nav_content.get('src', '')

                # 解析 filepos 位置信息
                if 'filepos' in src:
                    import re
                    match = re.search(r'filepos(\d+)', src)
                    if match:
                        pos = int(match.group(1))

                        # 在HTML中查找对应的锚点
                        anchor = f'<a id="filepos{pos}" />'.encode('utf-8')
                        anchor_pos = html_bytes.find(anchor)

                        if anchor_pos != -1:
                            # 从锚点之后查找实际的章节标题
                            label_bytes = label.encode('utf-8')
                            title_pos = html_bytes.find(label_bytes, anchor_pos)

                            if title_pos != -1:
                                # 找到章节标题标签的结束位置 </font></p>
                                title_end = html_bytes.find(b'</font></p>', title_pos)
                                if title_end != -1:
                                    # 找到段落标签 <p height="4em"...>
                                    paragraph_start = html_bytes.find(b'<p height="4em"', title_end)
                                    if paragraph_start != -1:
                                        # 找到段落标签结束位置 '>'
                                        paragraph_tag_end = html_bytes.find(b'>', paragraph_start)
                                        if paragraph_tag_end != -1:
                                            actual_pos = paragraph_tag_end + 1
                                        else:
                                            actual_pos = paragraph_start
                                    else:
                                        # 如果找不到段落标签，使用标题结束位置
                                        actual_pos = title_end + 10
                                else:
                                    # 找到章节标题后的段落标签结束位置
                                    paragraph_start = html_bytes.find(b'<p height="4em"', title_pos)
                                    if paragraph_start != -1:
                                        # 找到段落标签结束位置 '>'
                                        paragraph_tag_end = html_bytes.find(b'>', paragraph_start)
                                        if paragraph_tag_end != -1:
                                            actual_pos = paragraph_tag_end + 1
                                        else:
                                            actual_pos = paragraph_start
                                    else:
                                        # 如果找不到，使用标题位置
                                        actual_pos = title_pos

                                toc_data.append((anchor_pos, actual_pos, label))

        return toc_data
    except Exception as e:
        print(f"解析 NCX 文件失败: {e}")
        return []


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
            # 以二进制模式读取文件以支持字节位置
            with open(extracted_file, 'rb') as f:
                html_bytes = f.read()

            # 转换为字符串以用于BeautifulSoup处理
            html_content = html_bytes.decode('utf-8', errors='ignore')

            # 检查是否有 toc.ncx 文件
            toc_path = Path(tempdir) / "mobi7" / "toc.ncx"
            toc_data = _extract_mobi_toc_from_ncx(toc_path, html_bytes)

            if toc_data:
                # 使用 NCX 提供的位置信息来分割HTML文本
                all_text_parts = []

                # 按位置排序
                toc_data.sort(key=lambda x: x[0])

                # 从第一个章节开始处理
                prev_content_pos = toc_data[0][1]  # 第一个章节的内容开始位置
                prev_anchor_pos = toc_data[0][0]  # 第一个章节的锚点位置

                # 先插入第一个章节标题
                all_text_parts.append(f"{CHAPTER_MARKER} {toc_data[0][2]}")

                # 从第二个章节开始处理
                for i in range(1, len(toc_data)):
                    anchor_pos, content_pos, chapter_title = toc_data[i]

                    # 使用锚点位置作为分割点
                    if anchor_pos > prev_content_pos and anchor_pos < len(html_bytes):
                        # 提取位置前的HTML片段（字节）
                        html_fragment_bytes = html_bytes[prev_content_pos:anchor_pos]
                        # 解码为字符串
                        html_fragment = html_fragment_bytes.decode('utf-8', errors='ignore')
                        # 使用BeautifulSoup提取纯文本
                        fragment_soup = BeautifulSoup(html_fragment, 'html.parser')
                        fragment_text = fragment_soup.get_text(separator='\n', strip=True)

                        if fragment_text and len(fragment_text) > 10:
                            all_text_parts.append(fragment_text)

                        # 插入章节标题
                        all_text_parts.append(f"{CHAPTER_MARKER} {chapter_title}")

                        prev_anchor_pos = anchor_pos
                        prev_content_pos = content_pos

                # 添加最后一部分文本
                if prev_content_pos < len(html_bytes):
                    final_html_bytes = html_bytes[prev_content_pos:]
                    final_html = final_html_bytes.decode('utf-8', errors='ignore')
                    final_soup = BeautifulSoup(final_html, 'html.parser')
                    final_text = final_soup.get_text(separator='\n', strip=True)

                    if final_text and len(final_text) > 10:
                        all_text_parts.append(final_text)

                text = '\n\n'.join(all_text_parts)
            else:
                # 没有 NCX，尝试从 HTML 文件中提取章节标题（h1, h2, h3）
                soup = BeautifulSoup(html_content, 'html.parser')
                chapter_elements = soup.find_all(['h1', 'h2', 'h3'])

                if chapter_elements:
                    # 如果找到章节标题，使用它们来分割文本
                    all_text_parts = []

                    # 按顺序收集所有内容
                    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div']):
                        tag = element.name
                        text = element.get_text(strip=True)
                        if not text or len(text) <= 2:
                            continue

                        if tag in ['h1', 'h2', 'h3']:
                            # 章节标题
                            all_text_parts.append(f"{CHAPTER_MARKER} {text}")
                        else:
                            # 普通段落
                            all_text_parts.append(text)

                    text = '\n\n'.join(all_text_parts)
                else:
                    # 没有找到章节标题，直接提取所有文本
                    text = soup.get_text(separator=' ', strip=True)

            # 提取书名
            soup = BeautifulSoup(html_content, 'html.parser')
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
