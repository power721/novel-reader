"""
播放工作线程 - 后台播放音频
"""
from PySide6.QtCore import QThread, Signal
from typing import Optional


class PlaybackWorker(QThread):
    """播放工作线程，在后台执行播放任务"""

    # 信号定义
    finished = Signal()  # 播放完成
    error = Signal(str)  # 播放错误
    progress_updated = Signal(int, int)  # 进度更新，参数：current, total
    chapter_finished = Signal(int, int)  # 章节播放完成，参数：current_chunk, next_chapter_start_chunk
    last_chunk_of_chapter_started = Signal(int)  # 章节最后一个chunk开始播放，参数：next_chapter_start_chunk

    def __init__(self, book_id: int, start_chunk: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.book_id = book_id
        self.start_chunk = start_chunk
        self._is_running = True

    def run(self):
        """执行播放任务"""
        print(f"[DEBUG] PlaybackWorker.run() called: book_id={self.book_id}, start_chunk={self.start_chunk}")
        try:
            from novel_reader.core.player import play_audio, stop_playback
            from novel_reader.utils import load_txt_file, parse_txt
            from novel_reader.core import get_book, get_book_chapters
            from novel_reader.core.tts import AUDIO_DIR
            from pathlib import Path
            import os
            import subprocess

            # 获取书籍和章节信息
            book = get_book(self.book_id)
            if not book:
                raise ValueError(f"书籍不存在: book_id={self.book_id}")

            text = load_txt_file(book['file_path'])
            chunks, _ = parse_txt(text)
            total_chunks = len(chunks)
            chapters = get_book_chapters(self.book_id)

            # 计算起始位置
            start = self.start_chunk if self.start_chunk is not None else book['current_chunk']

            print(f"[DEBUG] PlaybackWorker: starting playback from chunk {start}, total {total_chunks}")
            print(f"[DEBUG] Chapters: {len(chapters)}")

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

            print(f"[DEBUG] Chapter boundaries: {chapter_boundaries}")

            # 检查音频目录
            book_audio_dir = AUDIO_DIR / str(self.book_id)
            if not book_audio_dir.exists():
                self.error.emit("音频目录不存在，请先进行TTS转换")
                return

            # 播放循环
            played_count = 0
            skipped_count = 0

            for chunk_id in range(start, total_chunks):
                # 检查是否应该停止
                if not self._is_running:
                    print("\n⏹ 播放已停止")
                    break

                # 检查是否是章节的最后一个chunk，如果是则提前转换下一章
                if chunk_id in chapter_boundaries and chunk_id > start:
                    next_chapter_start = chapter_boundaries[chunk_id]
                    print(f"🔄 [DEBUG] 即将播放章节最后一个chunk {chunk_id}，提前转换下一章 chunk {next_chapter_start}")
                    self.last_chunk_of_chapter_started.emit(next_chapter_start)

                audio_path = book_audio_dir / f"chunk_{chunk_id:05d}.wav"

                # 检查音频文件是否存在，如果不存在则等待TTS转换完成
                if not audio_path.exists():
                    print(f"⏳ [Chunk {chunk_id}] 音频文件不存在，等待TTS转换...")
                    import time
                    max_wait = 120  # 最多等待120秒（2分钟）
                    waited = 0
                    file_ready = False

                    while waited < max_wait and self._is_running:
                        if audio_path.exists():
                            file_size = audio_path.stat().st_size
                            if file_size > 20000:  # 大于20KB认为有效
                                file_ready = True
                                print(f"✅ [Chunk {chunk_id}] 音频文件就绪 ({file_size/1024:.1f} KB)")
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

                # 播放 chunk
                print(f"▶ [Chunk {chunk_id}/{total_chunks-1}] 正在播放...")
                try:
                    play_audio(str(audio_path))
                    played_count += 1
                except FileNotFoundError as e:
                    print(f"❌ [Chunk {chunk_id}] 播放失败: {e}")
                    skipped_count += 1
                    continue

                # 更新播放进度
                from novel_reader.core.player import update_progress
                update_progress(self.book_id, chunk_id)
                self.progress_updated.emit(chunk_id + 1, total_chunks)

                # 检查是否刚播放完一个章节的最后一个chunk
                if chunk_id in chapter_boundaries:
                    next_chapter_start = chapter_boundaries[chunk_id]
                    print(f"📖 [DEBUG] 章节播放完成: chunk {chunk_id}，下一章从 chunk {next_chapter_start} 开始")
                    self.chapter_finished.emit(chunk_id, next_chapter_start)

            # 播放总结
            print(f"\n✅ 播放完成")
            print(f"📊 统计: 成功播放 {played_count} 个，跳过 {skipped_count} 个")
            if skipped_count > 0:
                print(f"💡 提示: 已自动删除小于20KB的损坏文件")
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
        from novel_reader.core.player import stop_playback
        stop_playback()
        self.terminate()
