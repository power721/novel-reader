"""
播放工作线程 - 后台播放音频
"""
from PySide6.QtCore import QThread, Signal
from typing import Optional
from pathlib import Path


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


class PlaybackWorker(QThread):
    """播放工作线程，在后台执行播放任务"""

    # 信号定义
    finished = Signal()  # 播放完成
    error = Signal(str)  # 播放错误
    progress_updated = Signal(int, int)  # 进度更新，参数：current, total
    chapter_finished = Signal(int, int)  # 章节播放完成，参数：current_chunk, next_chapter_start_chunk
    last_chunk_of_chapter_started = Signal(int)  # 章节最后一个chunk开始播放，参数：next_chapter_start_chunk
    chapter_index_changed = Signal(int)  # 章节索引变化，参数：current_chunk
    chunks_conversion_requested = Signal(list)  # 请求转换chunk列表，参数：chunk_id列表

    def __init__(self, book_id: int, start_chunk: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self.start_chunk = start_chunk
        self._is_running = True
        self._is_paused = False  # 添加暂停标志
        self._current_chapter_index: Optional[int] = None  # Track current chapter index
        self._requested_chunks = set()  # 记录已请求转换的chunk，避免重复请求

    def run(self):
        """执行播放任务"""
        # Log the TTS engine being used
        from novel_reader.core import get_setting
        tts_engine = get_setting("tts_engine", "piper")
        print(f"[DEBUG] PlaybackWorker: TTS engine = {tts_engine}")

        try:
            from novel_reader.core.player import play_audio, stop_playback
            from novel_reader.utils import parse_txt_cached
            from novel_reader.core import get_book, get_book_chapters
            from novel_reader.core.tts import AUDIO_DIR
            from pathlib import Path
            import os
            import subprocess

            # 获取书籍和章节信息
            book = get_book(self.book_id)
            if not book:
                raise ValueError(f"书籍不存在: book_id={self.book_id}")

            # 使用带缓存的解析方法
            chunks, _ = parse_txt_cached(self.book_id, book)
            total_chunks = len(chunks)
            chapters = get_book_chapters(self.book_id)

            # 计算起始位置
            start = self.start_chunk if self.start_chunk is not None else book['current_chunk']

            # 发送初始进度
            self.progress_updated.emit(start, total_chunks)

            # 构建章节边界映射: chunk_id -> 下一章的起始chunk
            chapter_boundaries = {}
            for i, chapter in enumerate(chapters):
                chapter_start = chapter['start_chunk']
                if i + 1 < len(chapters):
                    next_chapter_start = chapters[i + 1]['start_chunk']
                    # 当前章节的最后一个chunk是下一章开始前的那个
                    last_chunk_of_chapter = next_chapter_start - 1
                    chapter_boundaries[last_chunk_of_chapter] = next_chapter_start

            # print(f"[DEBUG] Chapter boundaries: {chapter_boundaries}")

            # 检查音频目录
            book_audio_dir = AUDIO_DIR / str(self.book_id)
            if not book_audio_dir.exists():
                book_audio_dir.mkdir(parents=True, exist_ok=True)
                # self.error.emit("音频目录不存在，请先进行TTS转换")
                # return

            # 播放循环
            played_count = 0
            skipped_count = 0

            # Helper function to get chapter index for a chunk
            def get_chapter_index_for_chunk(cid: int) -> int:
                """获取指定chunk所属的章节索引（从0开始）"""
                for i, chapter in enumerate(chapters):
                    chapter_start = chapter['start_chunk']
                    if i + 1 < len(chapters):
                        next_chapter_start = chapters[i + 1]['start_chunk']
                        if chapter_start <= cid < next_chapter_start:
                            return i
                    else:
                        if chapter_start <= cid:
                            return i
                return 0

            for chunk_id in range(start, total_chunks):
                # 检查是否应该停止
                if not self._is_running:
                    print("\n⏹ 播放已停止")
                    break

                # 检查是否暂停，如果暂停则等待恢复
                while self._is_paused and self._is_running:
                    import time
                    time.sleep(0.1)  # 每100ms检查一次是否恢复
                    if not self._is_running:
                        print("\n⏹ 播放已停止")
                        break
                    if not self._is_paused:
                        print("▶️ 恢复播放")
                        break

                if not self._is_running:
                    break

                # 检查是否是章节的最后一个chunk，如果是则提前转换下一章
                if chunk_id in chapter_boundaries and chunk_id > start:
                    next_chapter_start = chapter_boundaries[chunk_id]
                    # print(f"🔄 [DEBUG] 即将播放章节最后一个chunk {chunk_id}，提前转换下一章 chunk {next_chapter_start}")
                    self.last_chunk_of_chapter_started.emit(next_chapter_start)

                # 跳过只包含省略号的分段
                chunk_text = chunks[chunk_id]
                if _is_meaningless_chunk(chunk_text):
                    print(f"⏭ [Chunk {chunk_id}] 跳过省略号分段")
                    skipped_count += 1
                    # 更新播放进度，以便继续播放下一个分段
                    from novel_reader.core.player import update_progress
                    update_progress(self.book_id, chunk_id)
                    self.progress_updated.emit(chunk_id + 1, total_chunks)
                    continue

                # 获取当前设置的模型ID和TTS引擎
                from novel_reader.core import get_setting
                tts_engine = get_setting("tts_engine", "piper")
                chinese_model_id = get_setting("chinese_model_id", "xiao_ya")

                # 根据TTS引擎确定音频文件路径
                if tts_engine == "edge":
                    # Edge TTS format: chunk_edge_{voice_id}_{chunk_id:05d}.mp3
                    edge_voice_id = get_setting("edge_chinese_voice_id", "xiaoxiao")
                    audio_path = book_audio_dir / f"chunk_edge_{edge_voice_id}_{chunk_id:05d}.mp3"
                else:
                    # Piper TTS format: chunk_{model_id}_{chunk_id:05d}.wav
                    audio_path = book_audio_dir / f"chunk_{chinese_model_id}_{chunk_id:05d}.wav"

                # print(f"[DEBUG PlaybackWorker] TTS engine={tts_engine}, audio_path={audio_path}")

                # 检查当前chunk音频文件是否存在
                file_needs_conversion = False

                if not audio_path.exists():
                    # print(f"⏳ [Chunk {chunk_id}] 音频文件不存在 ({audio_path.name})，请求转换...")
                    file_needs_conversion = True
                else:
                    # File exists, check size
                    file_size = audio_path.stat().st_size
                    # print(f"✅ [Chunk {chunk_id}] 音频文件存在: {audio_path.name} ({file_size / 1024:.1f} KB)")

                    if file_size < 5000:
                        print(f"⚠️ [Chunk {chunk_id}] 文件过小 ({file_size} < 5000)，可能损坏，删除并重新转换...")
                        audio_path.unlink()
                        file_needs_conversion = True

                if file_needs_conversion:
                    # print(f"⏳ [Chunk {chunk_id}] 请求转换...")
                    self.chunks_conversion_requested.emit([chunk_id])

                    # 等待TTS转换完成
                    import time
                    max_wait = 30  # 最多等待30秒
                    waited = 0
                    file_ready = False

                    while waited < max_wait and self._is_running:
                        if audio_path.exists():
                            file_size = audio_path.stat().st_size
                            if file_size > 5000:  # 大于5KB认为有效
                                file_ready = True
                                print(f"✅ [Chunk {chunk_id}] 音频文件就绪 ({file_size / 1024:.1f} KB)")
                                break
                        time.sleep(0.5)  # 每0.5秒检查一次
                        waited += 0.5

                    if not file_ready:
                        print(f"⏭ [Chunk {chunk_id}] 等待{max_wait}秒后仍未就绪，跳过")
                        skipped_count += 1
                        # 更新播放进度（即使是跳过的也要更新）
                        from novel_reader.core.player import update_progress
                        update_progress(self.book_id, chunk_id)
                        self.progress_updated.emit(chunk_id + 1, total_chunks)
                        continue

                # 当前chunk准备好后，再预转换后续chunk（从下一个开始）
                from novel_reader.core import get_setting
                prefetch_count = get_setting("prefetch_chunk_count", 3)
                chunks_to_convert = []

                # 收集后续需要预转换的chunk
                for offset in range(1, prefetch_count + 1):
                    target_chunk = chunk_id + offset
                    if target_chunk >= total_chunks:
                        break
                    chunks_to_convert.append(target_chunk)

                # 发出预转换请求信号
                if chunks_to_convert:
                    # print(f"🔄 [Chunk {chunk_id}] 预转换后续chunks: {chunks_to_convert}")
                    self.chunks_conversion_requested.emit(chunks_to_convert)

                # 在播放前更新进度和章节索引，这样点击"下一章"时能获取到实时位置
                from novel_reader.core.player import update_progress
                update_progress(self.book_id, chunk_id)

                # 检查章节是否变化，如果变化则发出信号
                new_chapter_index = get_chapter_index_for_chunk(chunk_id)
                if new_chapter_index != self._current_chapter_index:
                    self._current_chapter_index = new_chapter_index
                    self.chapter_index_changed.emit(chunk_id)

                # 播放前发送进度更新信号（让文本显示同步）
                self.progress_updated.emit(chunk_id, total_chunks)

                # 播放 chunk
                # print(f"▶ [Chunk {chunk_id}/{total_chunks - 1}] 正在播放...")
                try:
                    # 传入停止检查函数，让 play_audio 可以响应停止请求
                    play_audio(str(audio_path), should_stop_check_fn=lambda: not self._is_running)
                    played_count += 1
                except FileNotFoundError as e:
                    print(f"❌ [Chunk {chunk_id}] 播放失败: {e}")
                    print(f"🔄 [Chunk {chunk_id}] 重新请求转换...")

                    # 从已请求集合中移除，允许重新请求
                    self._requested_chunks.discard(chunk_id)

                    # 重新发出转换请求
                    self._requested_chunks.add(chunk_id)
                    self.chunks_conversion_requested.emit([chunk_id])
                    print(f"🔄 [Chunk {chunk_id}] 转换请求已发出，等待转换完成...")

                    # 等待TTS转换重新生成该文件
                    import time
                    max_wait = 30  # 最多等待30秒
                    waited = 0
                    file_ready = False

                    while waited < max_wait and self._is_running:
                        if audio_path.exists():
                            file_size = audio_path.stat().st_size
                            if file_size > 5000:  # 大于5KB认为有效
                                file_ready = True
                                print(f"✅ [Chunk {chunk_id}] 重新转换完成 ({file_size / 1024:.1f} KB)，重试播放")
                                break
                        time.sleep(1.0)  # 每1秒检查一次
                        waited += 1

                    if file_ready:
                        # 重试播放
                        try:
                            play_audio(str(audio_path), should_stop_check_fn=lambda: not self._is_running)
                            played_count += 1
                            print(f"✅ [Chunk {chunk_id}] 重试播放成功")
                        except FileNotFoundError as retry_error:
                            print(f"❌ [Chunk {chunk_id}] 重试失败: {retry_error}")
                            skipped_count += 1
                    else:
                        print(f"⏭ [Chunk {chunk_id}] 等待{max_wait}秒后仍未就绪，跳过")
                        skipped_count += 1

                # 更新进度到下一个chunk
                self.progress_updated.emit(chunk_id + 1, total_chunks)

                # 清理旧的音频文件
                self._cleanup_old_chunks(chunk_id, book_audio_dir)

                # 检查是否刚播放完一个章节的最后一个chunk
                if chunk_id in chapter_boundaries:
                    next_chapter_start = chapter_boundaries[chunk_id]
                    print(f"📖 [DEBUG] 章节播放完成: chunk {chunk_id}，下一章从 chunk {next_chapter_start} 开始")
                    self.chapter_finished.emit(chunk_id, next_chapter_start)

            # 播放总结
            print(f"\n✅ 播放完成")
            print(f"📊 统计: 成功播放 {played_count} 个，跳过 {skipped_count} 个")
            if skipped_count > 0:
                print(f"💡 提示: 已自动删除小于5KB的损坏文件")
                print(f"💡 建议: 请转换相关章节以继续播放")

        except Exception as e:
            import traceback
            print(f"[ERROR] PlaybackWorker error: {e}")
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        """停止播放"""
        self._is_running = False
        self._is_paused = False  # 重置暂停状态
        from novel_reader.core.player import stop_playback
        stop_playback()
        # Don't use terminate() - it forcefully kills the thread
        # The thread will exit gracefully when _is_running is False
        if not self.wait(3000):  # Wait up to 3 seconds for graceful shutdown
            print("[PlaybackWorker] Warning: Thread did not stop gracefully, forcing termination")
            self.terminate()
            self.wait()

    def pause(self):
        """暂停播放"""
        if self._is_running and not self._is_paused:
            self._is_paused = True
            # 使用 mpv 的原生暂停功能
            from novel_reader.core.player import pause_mpv
            success = pause_mpv()
            if not success:
                # 如果 IPC 失败，回退到停止方式
                print("⚠️ IPC暂停失败，使用停止方式")
                from novel_reader.core.player import stop_playback
                stop_playback()

    def resume(self):
        """恢复播放"""
        if self._is_paused:
            self._is_paused = False
            # 使用 mpv 的原生恢复功能
            from novel_reader.core.player import resume_mpv
            success = resume_mpv()
            if not success:
                # 如果 IPC 失败，记录警告
                print("⚠️ IPC恢复失败，音频可能已停止")

    def _cleanup_old_chunks(self, current_chunk: int, book_audio_dir: Path):
        """清理旧的音频文件"""
        from novel_reader.core import get_setting

        threshold = get_setting("cleanup_old_chunk_threshold", 50)
        keep_chunk_index = max(0, current_chunk - threshold)

        # print(f"[PlaybackWorker] 🔍 Cleanup: current={current_chunk}, threshold={threshold}, keep_after={keep_chunk_index}")

        if keep_chunk_index <= 0:
            return

        if not book_audio_dir.exists():
            return

        deleted = 0
        checked = 0

        for audio_file in book_audio_dir.glob("chunk_*.wav"):
            checked += 1
            try:
                # Handle both Piper (chunk_{model_id}_{chunk_id:05d}.wav)
                # and Edge TTS (chunk_edge_{voice_id}_{chunk_id:05d}.wav) formats
                chunk_id_str = audio_file.stem.split('_')
                if len(chunk_id_str) < 3:
                    continue

                # The chunk_id is always the last part
                chunk_id = int(chunk_id_str[-1])
                if chunk_id < keep_chunk_index:
                    audio_file.unlink()
                    deleted += 1
                    # print(f"[PlaybackWorker] 🗑 Deleted: {audio_file.name} (chunk {chunk_id})")
            except (ValueError, IndexError) as e:
                print(f"[PlaybackWorker] ⚠️ Parse error: {audio_file.name} - {e}")
                continue

        for audio_file in book_audio_dir.glob("chunk_*.mp3"):
            checked += 1
            try:
                # Handle both Piper (chunk_{model_id}_{chunk_id:05d}.wav)
                # and Edge TTS (chunk_edge_{voice_id}_{chunk_id:05d}.wav) formats
                chunk_id_str = audio_file.stem.split('_')
                if len(chunk_id_str) < 3:
                    continue

                # The chunk_id is always the last part
                chunk_id = int(chunk_id_str[-1])
                if chunk_id < keep_chunk_index:
                    audio_file.unlink()
                    deleted += 1
                    # print(f"[PlaybackWorker] 🗑 Deleted: {audio_file.name} (chunk {chunk_id})")
            except (ValueError, IndexError) as e:
                print(f"[PlaybackWorker] ⚠️ Parse error: {audio_file.name} - {e}")
                continue

        # if deleted > 0:
        #     print(f"[PlaybackWorker] ✅ Cleaned up {deleted}/{checked} old audio files (before chunk {keep_chunk_index})")
        # else:
        #     print(f"[PlaybackWorker] ℹ️ No files to delete (checked {checked} files)")
