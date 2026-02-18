"""
播放器模块 - 使用 mpv 播放音频，支持断点续播
"""
import subprocess
import os
import sqlite3
from pathlib import Path
from typing import Optional

from novel_reader.models import get_conn

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

# 音量控制 (0.0 - 1.0)
_volume = 1.0

# 播放速度 (0.5 - 2.0, 默认1.0)
_playback_speed = 1.0

# IPC socket 文件（用于实时控制 mpv）
_ipc_socket = "/tmp/novel-reader-mpv.sock"


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

    # 读取并解析文本（使用缓存）
    from novel_reader.utils import parse_txt_cached
    chunks, chapters = parse_txt_cached(book_id, {'file_path': file_path})

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
    from novel_reader.core import get_setting
    chinese_model_id = get_setting("chinese_model_id", "xiao_ya")
    available_chunks = 0
    missing_chunks = []
    for chunk_id in range(start_chunk, len(chunks)):
        audio_path = book_audio_dir / f"chunk_{chinese_model_id}_{chunk_id:05d}.wav"
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
            audio_path = AUDIO_DIR / str(book_id) / f"chunk_{chinese_model_id}_{chunk_id:05d}.wav"

            # 检查音频文件是否存在
            if not os.path.exists(audio_path):
                print(f"⏭ [Chunk {chunk_id}] 音频文件不存在，跳过")
                skipped_count += 1
                continue

            # 播放 chunk
            print(f"▶ [Chunk {chunk_id}/{len(chunks) - 1}] 正在播放...")
            try:
                play_audio(str(audio_path), should_stop_check_fn=lambda: _playback_state["should_stop"])
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
            print(f"💡 提示: 已自动删除小于5KB的损坏文件")
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
    from novel_reader.core import get_setting
    chinese_model_id = get_setting("chinese_model_id", "xiao_ya")
    audio_path = AUDIO_DIR / str(book_id) / f"chunk_{chinese_model_id}_{chunk_id:05d}.wav"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    print(f"播放 chunk {chunk_id}: {audio_path}")
    play_audio(str(audio_path), should_stop_check_fn=lambda: _playback_state["should_stop"])

    # 更新播放进度
    update_progress(book_id, chunk_id)


def play_audio(file_path: str, should_stop_check_fn=None) -> None:
    """
    使用 mpv 播放音频文件

    Args:
        file_path: 音频文件路径
        should_stop_check_fn: 可选的停止检查函数，定期调用以判断是否应该停止播放

    Raises:
        FileNotFoundError: 如果 mpv 不存在或音频文件不存在
    """
    global _playback_state

    # 检查音频文件是否存在
    if not os.path.exists(file_path):
        print(f"[player.play_audio] ERROR: Audio file not found: {file_path}")
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
    if file_size < 5000:  # 小于5KB可能损坏
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
    # --volume: 音量 (0-100)
    # --speed: 播放速度 (0.5-2.0)
    # --input-ipc-server: 启用 IPC 用于实时控制
    volume_percent = int(_volume * 100)
    cmd = [
        MPV_BIN,
        "--no-video",
        "--really-quiet",
        f"--volume={volume_percent}",
        f"--speed={_playback_speed}",
        f"--input-ipc-server={_ipc_socket}",
        file_path
    ]
    print(f"[player.play_audio] DEBUG: mpv command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        _playback_state["current_process"] = process

        # 等待播放完成，定期检查是否应该停止
        import time
        check_interval = 0.1  # 每100ms检查一次
        waited = 0
        while waited < PLAY_TIMEOUT:
            if should_stop_check_fn and should_stop_check_fn():
                print(f"[player.play_audio] INFO: Stop requested, terminating process")
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                # 正常退出，不检查返回码
                _playback_state["current_process"] = None
                return

            # 检查进程是否已结束
            if process.poll() is not None:
                # 进程已结束
                break

            time.sleep(check_interval)
            waited += check_interval

        # 检查返回码（只有在非停止请求结束时才检查）
        if process.poll() is not None and process.returncode != 0:
            # 检查是否是因为停止请求而结束的
            if should_stop_check_fn and should_stop_check_fn():
                # 是停止请求导致的结束，不报错
                _playback_state["current_process"] = None
                return

            # 获取错误输出
            _, stderr = process.communicate(timeout=1)
            error_msg = stderr.decode('utf-8', errors='ignore').strip()

            print(f"  ⚠ 播放失败 (返回码: {process.returncode})")
            print(f"  📁 文件路径: {file_path}")
            print(f"  📏 文件大小: {file_size:,} bytes")

            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"  ❌ 音频文件丢失: {file_path}")
            else:
                print(f"  💡 提示: 文件可能损坏，建议重新转换")
                print(f"  🔧 测试测试命令: mpv --no-video \"{file_path}\"")

                # 尝试获取更多信息
                if file_size < 100:
                    print(f"  ❌ 文件过小，可能是转换失败")

    except FileNotFoundError:
        print(f"[player.play_audio] ERROR: mpv not found!")
        raise FileNotFoundError(
            f"mpv 未找到，请确保已安装 mpv\n"
            f"安装方法: sudo apt install mpv"
        )
    except Exception as e:
        print(f"[player.play_audio] ERROR: Unexpected error: {e}")
        import traceback
        print(f"[player.play_audio] ERROR: Traceback:\n{traceback.format_exc()}")
        raise
    finally:
        _playback_state["current_process"] = None


def stop_playback() -> None:
    """停止当前播放"""
    global _playback_state

    # 首先设置停止标志，让 play_audio() 能检测到
    _playback_state["should_stop"] = True

    if _playback_state["current_process"]:
        process = _playback_state["current_process"]

        # 先尝试优雅终止
        process.terminate()

        # 等待最多1秒，如果还没退出则强制终止
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            print(f"[player.stop_playback] Process didn't terminate, killing...")
            process.kill()
            try:
                process.wait(timeout=0.5)
            except:
                pass  # Already killed

    else:
        print(f"[player.stop_playback] No current process to stop")

    # 清理 IPC socket 文件
    try:
        if os.path.exists(_ipc_socket):
            os.remove(_ipc_socket)
            # print(f"[player.stop_playback] Removed IPC socket: {_ipc_socket}")
    except:
        pass


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
                       SET current_chunk   = ?,
                           current_chapter = ?,
                           last_played_at  = ?,
                           updated_at      = CURRENT_TIMESTAMP
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


def set_volume(volume: float) -> None:
    """
    设置音量

    Args:
        volume: 音量值 (0.0 - 1.0)
    """
    global _volume
    _volume = max(0.0, min(1.0, volume))
    print(f"音量设置为: {_volume * 100:.0f}%")


def get_volume() -> float:
    """
    获取当前音量

    Returns:
        音量值 (0.0 - 1.0)
    """
    return _volume


def adjust_volume(delta: float) -> None:
    """
    调整音量

    Args:
        delta: 音量变化量 (正数增大，负数减小)
    """
    set_volume(_volume + delta)


def set_playback_speed(speed: float) -> None:
    """
    设置播放速度

    Args:
        speed: 播放速度 (0.5 - 2.0, 1.0 为正常速度)
    """
    global _playback_speed
    _playback_speed = max(0.5, min(2.0, speed))
    print(f"播放速度设置为: {_playback_speed:.2f}x")


def get_playback_speed() -> float:
    """
    获取当前播放速度

    Returns:
        播放速度 (0.5 - 2.0)
    """
    return _playback_speed


def set_playback_speed_realtime(speed: float) -> None:
    """
    实时设置播放速度（控制正在运行的 mpv 进程）

    Args:
        speed: 播放速度 (0.5 - 2.0)
    """
    global _playback_speed
    _playback_speed = max(0.5, min(2.0, speed))

    # 如果 mpv 正在运行，通过 IPC 实时调整播放速度
    if _playback_state["current_process"] and os.path.exists(_ipc_socket):
        import socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(_ipc_socket)

            # 发送设置播放速度命令
            command = f'{{"command": ["set_property", "speed", {_playback_speed:.2f}]}}\n'
            sock.sendall(command.encode())

            sock.close()
            print(f"实时播放速度调整: {_playback_speed:.2f}x")
        except Exception as e:
            print(f"实时播放速度调整失败: {e}")
    else:
        print(f"播放速度设置为: {_playback_speed:.2f}x")


def set_volume_realtime(volume: float) -> None:
    """
    实时设置音量（控制正在运行的 mpv 进程）

    Args:
        volume: 音量值 (0.0 - 1.0)
    """
    global _volume
    _volume = max(0.0, min(1.0, volume))

    # 如果 mpv 正在运行，通过 IPC 实时调整音量
    if _playback_state["current_process"] and os.path.exists(_ipc_socket):
        import socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(_ipc_socket)

            # 发送设置音量命令
            volume_percent = int(_volume * 100)
            command = f'{{"command": ["set_property", "volume", {volume_percent}]}}\n'
            sock.sendall(command.encode())

            sock.close()
            print(f"实时音量调整: {volume_percent}%")
        except Exception as e:
            print(f"实时音量调整失败: {e}")
    else:
        print(f"音量设置为: {_volume * 100:.0f}%")


def check_mpv_installed() -> bool:
    """
    检查 mpv 是否已安装
    """
    import shutil
    return shutil.which(MPV_BIN) is not None


def pause_mpv() -> bool:
    """
    通过 IPC 暂停 mpv 播放

    Returns:
        bool: 是否成功暂停
    """
    if _playback_state["current_process"] and os.path.exists(_ipc_socket):
        import socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(_ipc_socket)

            # 发送暂停命令
            command = '{"command": ["set_property", "pause", true]}\n'
            sock.sendall(command.encode())

            sock.close()
            return True
        except Exception as e:
            print(f"暂停 mpv 失败: {e}")
            return False
    return False


def resume_mpv() -> bool:
    """
    通过 IPC 恢复 mpv 播放

    Returns:
        bool: 是否成功恢复
    """
    if _playback_state["current_process"] and os.path.exists(_ipc_socket):
        import socket
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(_ipc_socket)

            # 发送恢复命令
            command = '{"command": ["set_property", "pause", false]}\n'
            sock.sendall(command.encode())

            sock.close()
            return True
        except Exception as e:
            print(f"恢复 mpv 失败: {e}")
            return False
    return False


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
    from novel_reader.utils import parse_txt_cached

    book = get_book(book_id)
    if not book:
        return {"error": "书籍不存在"}

    # 使用带缓存的解析方法
    chunks, _ = parse_txt_cached(book_id, book)
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

    from novel_reader.core import get_setting
    chinese_model_id = get_setting("chinese_model_id", "xiao_ya")

    for chunk_id in range(total_chunks):
        audio_path = book_audio_dir / f"chunk_{chinese_model_id}_{chunk_id:05d}.wav"
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
            elif file_size < 5000:  # 小于5KB认为损坏
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

    print(f"\n{'=' * 60}")
    print(f"📖 书籍: {diagnosis['book_title']}")
    print(f"📚 总chunk数: {diagnosis['total_chunks']}")
    print(f"{'=' * 60}")
    print(f"✅ 存在: {diagnosis['existing']}")
    print(f"❌ 缺失: {diagnosis['missing']}")
    print(f"⚠ 空文件: {diagnosis['empty']}")
    print(f"⚠ 过小: {diagnosis['too_small']}")
    print(f"{'=' * 60}")
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
                print(
                    f"  {status_icon} Chunk {detail['chunk_id']:3d}: {detail['status']:15s} (大小: {size_kb:8.2f} KB)")


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

    from novel_reader.core import get_setting
    chinese_model_id = get_setting("chinese_model_id", "xiao_ya")

    for detail in diagnosis['details']:
        if detail['status'] in ['empty', 'too_small']:
            audio_path = book_audio_dir / f"chunk_{chinese_model_id}_{detail['chunk_id']:05d}.wav"
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
