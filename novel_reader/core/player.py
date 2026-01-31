"""
播放器模块 - 使用 mpv 播放音频，支持断点续播
"""
import subprocess
import os
import time
import sqlite3
from pathlib import Path
from typing import Optional

from novel_reader.models import get_conn
from novel_reader.utils import load_txt_file, parse_txt


# ==================== 配置区 ====================

# mpv 可执行文件路径
MPV_BIN = "mpv"

# 音频输出目录
AUDIO_DIR = Path("data/audio")

# 播放超时时间（秒）
PLAY_TIMEOUT = 3600

# 是否循环播放
LOOP = False

# ================================================

# 播放控制标志
_playback_state = {
    "should_stop": False,
    "should_pause": False,
    "current_process": None
}


def play_book(book_id: int, start_chunk: Optional[int] = None) -> None:
    """
    播放整本书，支持断点续播

    Args:
        book_id: 书籍 ID
        start_chunk: 起始 chunk ID（可选，默认从 current_chunk 开始）
    """
    global _playback_state

    conn = get_conn()
    cursor = conn.cursor()

    # 获取书籍信息
    cursor.execute("SELECT file_path, current_chunk FROM book WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    if not book:
        raise ValueError(f"书籍不存在: book_id={book_id}")

    file_path, current_chunk = book

    # 使用指定的起始 chunk 或数据库中的 current_chunk
    start_chunk = start_chunk if start_chunk is not None else current_chunk

    # 读取并解析文本
    text = load_txt_file(file_path)
    chunks, chapters = parse_txt(text)

    if start_chunk >= len(chunks):
        print(f"起始 chunk {start_chunk} 超出范围 (总共 {len(chunks)} 个)")
        return

    # 检查是否有可用的音频文件
    book_audio_dir = AUDIO_DIR / str(book_id)
    if not book_audio_dir.exists():
        print(f"\n❌ 错误: 音频目录不存在")
        print(f"📝 请先进行 TTS 转换！")
        print(f"💡 提示: 在 GUI 中选择书籍后点击「转换整本书」按钮")
        return

    # 统计可用的音频文件数量
    available_chunks = 0
    missing_chunks = []
    for chunk_id in range(start_chunk, len(chunks)):
        audio_path = book_audio_dir / f"chunk_{chunk_id:05d}.wav"
        if os.path.exists(audio_path):
            available_chunks += 1
        else:
            missing_chunks.append(chunk_id)

    if available_chunks == 0:
        print(f"\n❌ 错误: 没有可用的音频文件")
        print(f"📝 请先进行 TTS 转换！")
        print(f"💡 提示: 在 GUI 中选择书籍后点击「转换整本书」按钮")
        return

    if missing_chunks:
        print(f"\n⚠ 警告: 有 {len(missing_chunks)} 个音频文件缺失")
        print(f"缺失范围: chunk {min(missing_chunks)} - {max(missing_chunks)}")
        print(f"💡 建议: 转换缺失的章节或转换整本书")

    print(f"\n▶️ 开始播放: {Path(file_path).stem}")
    print(f"📍 起始位置: chunk {start_chunk} / {len(chunks) - 1}")
    print(f"✅ 可用音频: {available_chunks} / {len(chunks) - start_chunk}")
    print(f"按 Ctrl+C 停止播放\n")

    _playback_state["should_stop"] = False

    try:
        played_count = 0
        skipped_count = 0

        for chunk_id in range(start_chunk, len(chunks)):
            # 检查是否应该停止
            if _playback_state["should_stop"]:
                print("\n⏹ 播放已停止")
                break

            chunk_text = chunks[chunk_id]
            audio_path = AUDIO_DIR / str(book_id) / f"chunk_{chunk_id:05d}.wav"

            # 检查音频文件是否存在
            if not os.path.exists(audio_path):
                print(f"⏭ [Chunk {chunk_id}] 音频文件不存在，跳过")
                skipped_count += 1
                continue

            # 播放 chunk
            print(f"▶ [Chunk {chunk_id}/{len(chunks)-1}] 正在播放...")
            try:
                play_audio(str(audio_path))
                played_count += 1
            except FileNotFoundError as e:
                print(f"❌ [Chunk {chunk_id}] 播放失败: {e}")
                skipped_count += 1
                continue

            # 更新播放进度
            update_progress(book_id, chunk_id)

        # 播放总结
        print(f"\n✅ 播放完成")
        print(f"📊 统计: 成功播放 {played_count} 个，跳过 {skipped_count} 个")
        if skipped_count > 0:
            print(f"💡 提示: 已自动删除小于20KB的损坏文件")
            print(f"💡 建议: 请转换相关章节以继续播放")

    except KeyboardInterrupt:
        print("\n⏹ 播放已中断")
        # 进度已在循环中更新，无需额外处理

    finally:
        _playback_state["should_stop"] = False
        _playback_state["current_process"] = None


def play_chunk(book_id: int, chunk_id: int) -> None:
    """
    播放单个 chunk

    Args:
        book_id: 书籍 ID
        chunk_id: chunk ID
    """
    audio_path = AUDIO_DIR / str(book_id) / f"chunk_{chunk_id:05d}.wav"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    print(f"播放 chunk {chunk_id}: {audio_path}")
    play_audio(str(audio_path))

    # 更新播放进度
    update_progress(book_id, chunk_id)


def play_audio(file_path: str) -> None:
    """
    使用 mpv 播放音频文件

    Args:
        file_path: 音频文件路径

    Raises:
        FileNotFoundError: 如果 mpv 不存在或音频文件不存在
    """
    global _playback_state

    # 检查音频文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"音频文件不存在: {file_path}")

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        # 删除空文件
        try:
            os.remove(file_path)
            print(f"  🗑 已删除空文件: {file_path}")
        except:
            pass
        raise FileNotFoundError(f"音频文件为空，已删除: {file_path}")
    if file_size < 20000:  # 小于20KB可能损坏
        print(f"  ⚠ 警告: 文件大小异常 ({file_size} bytes)，删除并重新转换")
        try:
            os.remove(file_path)
            print(f"  🗑 已删除损坏文件: {file_path}")
        except:
            pass
        raise FileNotFoundError(f"音频文件过小，已删除: {file_path}")

    # 构建 mpv 命令
    # --no-video: 只播放音频
    # --really-quiet: 静默模式（减少输出）
    cmd = [MPV_BIN, "--no-video", "--really-quiet", file_path]

    try:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        _playback_state["current_process"] = process

        # 等待播放完成
        process.wait(timeout=PLAY_TIMEOUT)

        if process.returncode != 0:
            # 获取错误输出
            _, stderr = process.communicate()
            error_msg = stderr.decode('utf-8', errors='ignore').strip()

            print(f"  ⚠ 播放失败 (返回码: {process.returncode})")
            print(f"  📁 文件路径: {file_path}")
            print(f"  📏 文件大小: {file_size:,} bytes")

            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"  ❌ 音频文件丢失: {file_path}")
            else:
                print(f"  💡 提示: 文件可能损坏，建议重新转换")
                print(f"  🔧 测试命令: mpv --no-video \"{file_path}\"")

                # 尝试获取更多信息
                if file_size < 100:
                    print(f"  ❌ 文件过小，可能是转换失败")

    except subprocess.TimeoutExpired:
        process.kill()
        print(f"  ⏱ 播放超时")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"mpv 未找到，请确保已安装 mpv\n"
            f"安装方法: sudo apt install mpv"
        )
    finally:
        _playback_state["current_process"] = None


def stop_playback() -> None:
    """停止当前播放"""
    global _playback_state

    if _playback_state["current_process"]:
        _playback_state["current_process"].terminate()
        print("播放已停止")

    _playback_state["should_stop"] = True


def update_progress(book_id: int, chunk_id: int) -> None:
    """
    更新播放进度到数据库

    Args:
        book_id: 书籍 ID
        chunk_id: 当前 chunk ID
    """
    from datetime import datetime
    from novel_reader.core import get_book_chapters

    conn = get_conn()
    cursor = conn.cursor()

    try:
        # 查找当前 chunk 所属的章节
        chapters = get_book_chapters(book_id)
        current_chapter_id = 0

        for i, chapter in enumerate(chapters):
            chapter_start = chapter['start_chunk']
            # 检查是否是包含当前 chunk 的章节
            if i + 1 < len(chapters):
                next_chapter_start = chapters[i + 1]['start_chunk']
                if chapter_start <= chunk_id < next_chapter_start:
                    current_chapter_id = i + 1  # 章节编号从1开始
                    break
            else:
                # 最后一章
                if chapter_start <= chunk_id:
                    current_chapter_id = i + 1
                    break

        # 更新进度、章节和最后播放时间
        cursor.execute("""
            UPDATE book
            SET current_chunk = ?,
                current_chapter = ?,
                last_played_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (chunk_id, current_chapter_id, datetime.now().isoformat(), book_id))

        conn.commit()

    except sqlite3.Error as e:
        print(f"更新进度失败: {e}")

    finally:
        conn.close()


def get_progress(book_id: int) -> int:
    """
    获取书籍的播放进度

    Args:
        book_id: 书籍 ID

    Returns:
        当前 chunk ID
    """
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT current_chunk FROM book WHERE id = ?", (book_id,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            raise ValueError(f"书籍不存在: book_id={book_id}")

    finally:
        conn.close()


def reset_progress(book_id: int) -> None:
    """
    重置书籍的播放进度

    Args:
        book_id: 书籍 ID
    """
    update_progress(book_id, 0)
    print(f"已重置播放进度: book_id={book_id}")


def check_mpv_installed() -> bool:
    """
    检查 mpv 是否已安装

    Returns:
        True 如果 mpv 可用，否则 False
    """
    try:
        result = subprocess.run(
            [MPV_BIN, "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def diagnose_audio_files(book_id: int) -> dict:
    """
    诊断书籍的音频文件

    Args:
        book_id: 书籍 ID

    Returns:
        诊断结果字典
    """
    from novel_reader.core import get_book
    from novel_reader.utils import load_txt_file, parse_txt

    book = get_book(book_id)
    if not book:
        return {"error": "书籍不存在"}

    text = load_txt_file(book['file_path'])
    chunks, _ = parse_txt(text)
    total_chunks = len(chunks)

    book_audio_dir = AUDIO_DIR / str(book_id)

    result = {
        "book_id": book_id,
        "book_title": book['title'],
        "total_chunks": total_chunks,
        "existing": 0,
        "missing": 0,
        "empty": 0,
        "too_small": 0,
        "possibly_corrupted": 0,
        "details": []
    }

    for chunk_id in range(total_chunks):
        audio_path = book_audio_dir / f"chunk_{chunk_id:05d}.wav"
        chunk_info = {
            "chunk_id": chunk_id,
            "exists": False,
            "size": 0,
            "status": "missing"
        }

        if audio_path.exists():
            chunk_info["exists"] = True
            file_size = os.path.getsize(audio_path)
            chunk_info["size"] = file_size
            result["existing"] += 1

            if file_size == 0:
                chunk_info["status"] = "empty"
                result["empty"] += 1
            elif file_size < 20000:  # 小于20KB认为损坏
                chunk_info["status"] = "too_small"
                result["too_small"] += 1
            else:
                chunk_info["status"] = "ok"
        else:
            result["missing"] += 1

        result["details"].append(chunk_info)

    # 计算可能有问题的文件
    result["problematic"] = result["missing"] + result["empty"] + result["too_small"]

    return result


def print_diagnosis(diagnosis: dict) -> None:
    """
    打印诊断结果

    Args:
        diagnosis: diagnose_audio_files() 返回的诊断结果
    """
    if "error" in diagnosis:
        print(f"❌ 错误: {diagnosis['error']}")
        return

    print(f"\n{'='*60}")
    print(f"📖 书籍: {diagnosis['book_title']}")
    print(f"📚 总chunk数: {diagnosis['total_chunks']}")
    print(f"{'='*60}")
    print(f"✅ 存在: {diagnosis['existing']}")
    print(f"❌ 缺失: {diagnosis['missing']}")
    print(f"⚠ 空文件: {diagnosis['empty']}")
    print(f"⚠ 过小: {diagnosis['too_small']}")
    print(f"{'='*60}")
    print(f"📊 问题统计: {diagnosis['problematic']} / {diagnosis['total_chunks']}")

    if diagnosis['problematic'] > 0:
        print(f"\n🔍 问题详情:")
        for detail in diagnosis['details']:
            if detail['status'] != 'ok':
                status_icon = {
                    'missing': '❌',
                    'empty': '⚠',
                    'too_small': '⚠'
                }.get(detail['status'], '❓')
                size_kb = detail['size'] / 1024 if detail['size'] > 0 else 0
                print(f"  {status_icon} Chunk {detail['chunk_id']:3d}: {detail['status']:15s} (大小: {size_kb:8.2f} KB)")


def delete_corrupted_audio(book_id: int, diagnosis: dict = None) -> int:
    """
    删除损坏的音频文件

    Args:
        book_id: 书籍 ID
        diagnosis: 可选的诊断结果，如果为None会自动诊断

    Returns:
        删除的文件数量
    """
    if diagnosis is None:
        diagnosis = diagnose_audio_files(book_id)

    if "error" in diagnosis:
        return 0

    deleted_count = 0
    book_audio_dir = AUDIO_DIR / str(book_id)

    for detail in diagnosis['details']:
        if detail['status'] in ['empty', 'too_small']:
            audio_path = book_audio_dir / f"chunk_{detail['chunk_id']:05d}.wav"
            try:
                if audio_path.exists():
                    audio_path.unlink()
                    size_kb = detail['size'] / 1024
                    print(f"  🗑 已删除: chunk {detail['chunk_id']} ({size_kb:.2f} KB)")
                    deleted_count += 1
            except Exception as e:
                print(f"  ❌ 删除失败: chunk {detail['chunk_id']} - {e}")

    return deleted_count


if __name__ == "__main__":
    print("=" * 60)
    print("播放器模块测试")
    print("=" * 60)

    # 检查 mpv 是否安装
    print("\n[1] 检查 mpv 安装...")
    if check_mpv_installed():
        print("✓ mpv 已安装")
    else:
        print("✗ mpv 未安装")
        print("\n请安装 mpv:")
        print("  Ubuntu/Debian: sudo apt install mpv")
        print("  Arch: sudo pacman -S mpv")
        print("  macOS: brew install mpv")
        exit(1)

    # 初始化数据库
    from novel_reader.models import init_db
    init_db()

    # 创建测试书籍
    print("\n[2] 创建测试书籍...")
    test_file = "/tmp/test_novel_playback.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
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
""" * 20)

    # 导入书籍
    from novel_reader.core import import_book
    book_id = import_book(test_file)

    # 测试进度更新
    print("\n[3] 测试进度管理...")
    update_progress(book_id, 5)
    progress = get_progress(book_id)
    print(f"✓ 更新进度: chunk {progress}")

    progress = get_progress(book_id)
    print(f"✓ 读取进度: chunk {progress}")

    reset_progress(book_id)
    progress = get_progress(book_id)
    print(f"✓ 重置进度: chunk {progress}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n使用方法:")
    print("""
from novel_reader.core.player import play_book, play_chunk, stop_playback

# 播放整本书（从断点继续）
play_book(book_id=1)

# 播放整本书（从指定位置开始）
play_book(book_id=1, start_chunk=10)

# 播放单个 chunk
play_chunk(book_id=1, chunk_id=0)

# 停止播放
stop_playback()

# 获取播放进度
progress = get_progress(book_id=1)

# 重置播放进度
reset_progress(book_id=1)
    """)
