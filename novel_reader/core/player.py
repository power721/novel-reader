"""
播放器模块 - 使用 mpv 播放音频，支持断点续播
"""
import subprocess
import os
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from novel_reader.models import get_conn


class QtAudioPlayer(QObject):
    """QMediaPlayer wrapper for audiobook playback"""

    # Signals
    finished = Signal()  # Playback completed
    error = Signal(str)  # Playback error
    position_changed = Signal(int, int)  # current_ms, total_ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self._volume = 1.0
        self._playback_speed = 1.0
        self._is_playing = False
        self._is_paused = False

        # Create QMediaPlayer and QAudioOutput
        self._media_player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)

        # Connect audio output to media player
        self._media_player.setAudioOutput(self._audio_output)

        # Connect signals
        self._media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_player.errorOccurred.connect(self._on_error_occurred)
        self._media_player.positionChanged.connect(self._on_position_changed)

    def _on_media_status_changed(self, status):
        """Handle media status changes"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._is_playing = False
            self.finished.emit()
        elif status == QMediaPlayer.MediaStatus.Playing:
            # Media is actually playing now, set the state
            self._is_playing = True
            self._is_paused = False

    def _on_error_occurred(self, error, error_string):
        """Handle playback errors"""
        print(f"[QtAudioPlayer] Error: {error_string}")
        self.error.emit(error_string)

    def _on_position_changed(self, position):
        """Handle position changes during playback"""
        duration = self._media_player.duration()
        if duration > 0:
            self.position_changed.emit(position, duration)

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def play(self, audio_path: str, start_offset_ms: int = 0):
        """
        Play audio file

        Args:
            audio_path: Path to audio file
            start_offset_ms: Start position in milliseconds
        """
        # Check if file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Set audio source
        self._media_player.setSource(QUrl.fromLocalFile(audio_path))

        # Set volume
        self._audio_output.setVolume(self._volume)

        # Set playback speed
        self._media_player.setPlaybackRate(self._playback_speed)

        # Start playback
        self._media_player.play()

        # Handle start offset
        if start_offset_ms > 0:
            self._media_player.setPosition(start_offset_ms)

        # Note: State will be set by _on_media_status_changed() when media actually starts
        # QMediaPlayer loads media asynchronously, so we don't set _is_playing here
        # to avoid race conditions

        print(f"[QtAudioPlayer] ▶ Playing: {os.path.basename(audio_path)}")

    def stop(self):
        """Stop playback"""
        if self._is_playing or self._is_paused:
            self._media_player.stop()
            self._is_playing = False
            self._is_paused = False
            print("[QtAudioPlayer] ⏹ Stopped")

    def pause(self):
        """Pause playback"""
        if self._is_playing and not self._is_paused:
            self._media_player.pause()
            self._is_paused = True
            print("[QtAudioPlayer] ⏸ Paused")

    def resume(self):
        """Resume playback"""
        if self._is_paused:
            self._media_player.play()
            # Note: State will be set by _on_media_status_changed() when media actually starts
            print("[QtAudioPlayer] ▶ Resumed")

    def set_volume(self, volume: float):
        """
        Set volume

        Args:
            volume: Volume level (0.0 - 1.0)
        """
        self._volume = max(0.0, min(1.0, volume))
        self._audio_output.setVolume(self._volume)
        print(f"[QtAudioPlayer] 🔊 Volume: {int(self._volume * 100)}%")

    def set_playback_speed(self, speed: float):
        """
        Set playback speed

        Args:
            speed: Playback speed (0.5 - 2.0)
        """
        self._playback_speed = max(0.5, min(2.0, speed))
        self._media_player.setPlaybackRate(self._playback_speed)
        print(f"[QtAudioPlayer] ⏱ Speed: {self._playback_speed:.2f}x")

    def seek(self, offset_ms: int):
        """
        Seek to position

        Args:
            offset_ms: Position in milliseconds
        """
        self._media_player.setPosition(offset_ms)
        print(f"[QtAudioPlayer] ⏩ Seek to {offset_ms}ms")


# ==================== Singleton Instance ====================

# Singleton instance
_player: Optional[QtAudioPlayer] = None


def _get_player() -> QtAudioPlayer:
    """
    Get or create the singleton QtAudioPlayer instance

    Returns:
        QtAudioPlayer instance
    """
    global _player
    if _player is None:
        _player = QtAudioPlayer()
    return _player


# ==================== Legacy Functions ====================

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


def get_current_time() -> str:
    """
    获取当前时间的 ISO 格式字符串（带时区）

    Returns:
        ISO 8601 格式的时间字符串，包含 UTC 时区信息
    """
    return datetime.now(timezone.utc).isoformat()

# ==================== 配置区 ====================

# 音频输出目录
AUDIO_DIR = Path("data/audio")

# 播放超时时间（秒）
PLAY_TIMEOUT = 3600

# 是否循环播放
LOOP = False

# ================================================

# Old mpv global variables - deprecated, use QtAudioPlayer singleton instead
# _playback_state = {
#     "should_stop": False,
#     "should_pause": False,
#     "current_process": None
# }
# _volume = 1.0
# _playback_speed = 1.0
# _ipc_socket = "/tmp/novel-reader-mpv.sock"


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
    edge_voice_id = get_setting("edge_chinese_voice_id", "xiaoxiao")
    available_chunks = 0
    missing_chunks = []
    for chunk_id in range(start_chunk, len(chunks)):
        audio_path = book_audio_dir / f"chunk_edge_{edge_voice_id}_{chunk_id:05d}.mp3"
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

            # 跳过只包含省略号的分段
            if _is_meaningless_chunk(chunk_text):
                print(f"⏭ [Chunk {chunk_id}] 跳过省略号分段")
                skipped_count += 1
                # 更新播放进度，以便继续播放下一个分段
                update_progress(book_id, chunk_id)
                continue

            audio_path = AUDIO_DIR / str(book_id) / f"chunk_edge_{edge_voice_id}_{chunk_id:05d}.mp3"

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
    edge_voice_id = get_setting("edge_chinese_voice_id", "xiaoxiao")
    audio_path = AUDIO_DIR / str(book_id) / f"chunk_edge_{edge_voice_id}_{chunk_id:05d}.mp3"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    print(f"播放 chunk {chunk_id}: {audio_path}")
    play_audio(str(audio_path), should_stop_check_fn=lambda: _playback_state["should_stop"])

    # 更新播放进度
    update_progress(book_id, chunk_id)


def play_audio(file_path: str, should_stop_check_fn=None) -> None:
    """
    Play audio file using QMediaPlayer

    Args:
        file_path: Audio file path
        should_stop_check_fn: Optional callback to check if should stop (deprecated, kept for compatibility)

    Raises:
        FileNotFoundError: If audio file not found
    """
    # Check audio file exists
    if not os.path.exists(file_path):
        print(f"[player.play_audio] ERROR: Audio file not found: {file_path}")
        raise FileNotFoundError(f"音频文件不存在: {file_path}")

    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        try:
            os.remove(file_path)
            print(f"  🗑 已删除空文件: {file_path}")
        except:
            pass
        raise FileNotFoundError(f"音频文件为空，已删除: {file_path}")

    if file_size < 5000:
        print(f"  ⚠ 警告: 文件大小异常 ({file_size} bytes)，删除并重新转换")
        try:
            os.remove(file_path)
            print(f"  🗑 已删除损坏文件: {file_path}")
        except:
            pass
        raise FileNotFoundError(f"音频文件过小，已删除: {file_path}")

    # Get player instance and play
    player = _get_player()

    # Note: should_stop_check_fn is deprecated - stop is now handled via direct stop() call
    # PlaybackWorker will call stop_playback() directly when needed

    player.play(str(file_path))

    # Wait for playback to complete (blocking wait for compatibility)
    # In practice, PlaybackWorker manages the flow
    import time
    while player.is_playing and not player.is_paused:
        time.sleep(0.1)


def stop_playback() -> None:
    """Stop current playback"""
    global _player

    if _player:
        _player.stop()


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
        current_time = get_current_time()
        cursor.execute("""
                       UPDATE book
                       SET current_chunk   = ?,
                           current_chapter = ?,
                           last_played_at  = ?,
                           updated_at      = ?
                       WHERE id = ?
                       """, (chunk_id, current_chapter_id, current_time, current_time, book_id))

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
    Set volume

    Args:
        volume: Volume value (0.0 - 1.0)
    """
    player = _get_player()
    player.set_volume(volume)


def get_volume() -> float:
    """
    Get current volume

    Returns:
        Volume value (0.0 - 1.0)
    """
    player = _get_player()
    return player._volume


def adjust_volume(delta: float) -> None:
    """
    Adjust volume

    Args:
        delta: Volume change amount (positive to increase, negative to decrease)
    """
    current = get_volume()
    set_volume(current + delta)


def set_playback_speed(speed: float) -> None:
    """
    Set playback speed

    Args:
        speed: Playback speed (0.5 - 2.0, 1.0 is normal speed)
    """
    player = _get_player()
    player.set_playback_speed(speed)


def get_playback_speed() -> float:
    """
    Get current playback speed

    Returns:
        Playback speed (0.5 - 2.0)
    """
    player = _get_player()
    return player._playback_speed


def set_playback_speed_realtime(speed: float) -> None:
    """
    Set playback speed in real-time (during playback)

    Args:
        speed: Playback speed (0.5 - 2.0)
    """
    player = _get_player()
    player.set_playback_speed(speed)


def set_volume_realtime(volume: float) -> None:
    """
    Set volume in real-time (during playback)

    Args:
        volume: Volume value (0.0 - 1.0)
    """
    player = _get_player()
    player.set_volume(volume)


def check_mpv_installed() -> bool:
    """
    Check if Qt Multimedia is available

    Returns:
        True if available, False otherwise
    """
    try:
        from PySide6.QtMultimedia import QMediaPlayer
        return True
    except ImportError:
        return False


def pause_mpv() -> bool:
    """
    Pause playback

    Returns:
        True if successful, False otherwise
    """
    global _player

    if _player and _player.is_playing:
        _player.pause()
        return True
    return False


def resume_mpv() -> bool:
    """
    Resume playback

    Returns:
        True if successful, False otherwise
    """
    global _player

    if _player and _player.is_paused:
        _player.resume()
        return True
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
    edge_voice_id = get_setting("edge_chinese_voice_id", "xiaoxiao")

    for chunk_id in range(total_chunks):
        audio_path = book_audio_dir / f"chunk_edge_{edge_voice_id}_{chunk_id:05d}.mp3"
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
    edge_voice_id = get_setting("edge_chinese_voice_id", "xiaoxiao")

    for detail in diagnosis['details']:
        if detail['status'] in ['empty', 'too_small']:
            audio_path = book_audio_dir / f"chunk_edge_{edge_voice_id}_{detail['chunk_id']:05d}.mp3"
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
