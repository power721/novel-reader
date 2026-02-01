"""
TTS 工作线程 - 后台执行 TTS 转换
"""
from pathlib import Path

from PySide6.QtCore import QThread, Signal
import os
from typing import Optional, List

MIN_SIZE = 20000


class TTSWorker(QThread):
    """TTS 转换工作线程，在后台执行转换任务"""

    # 信号定义
    progress = Signal(int, int)  # 进度更新，参数：current, total
    log = Signal(str)  # 日志消息
    finished = Signal()  # 转换完成
    chapter_finished = Signal(int, int)  # 章节转换完成，参数：chapter_end_chunk, next_start_chunk
    first_chunk_ready = Signal(int)  # 第一个chunk转换完成，参数：start_chunk
    error = Signal(str)  # 转换错误

    def __init__(self, book_id: int, start_chunk: Optional[int] = None,
                 end_chunk: Optional[int] = None,
                 chapter_mode: bool = False, max_preview_chapters: int = 0, parent=None):
        """
        初始化 TTS Worker

        Args:
            book_id: 书籍 ID
            start_chunk: 起始 chunk ID（可选）
            end_chunk: 结束 chunk ID（不包含），用于指定转换范围
            chapter_mode: 是否为章节模式（转换当前章节后继续转换后续章节）
            max_preview_chapters: 预转换后续章节数量（默认0章，即只转换当前章节）
        """
        super().__init__(parent)
        self.book_id = book_id
        self.start_chunk = start_chunk
        self.end_chunk = end_chunk
        self.chapter_mode = chapter_mode
        self.max_preview_chapters = max_preview_chapters
        self._is_running = True

    def run(self):
        """执行 TTS 转换任务"""
        try:
            self.log.emit(f"[DEBUG] TTS Worker started: book_id={self.book_id}, start_chunk={self.start_chunk}, chapter_mode={self.chapter_mode}")

            from novel_reader.core import get_book, get_book_chapters
            from novel_reader.utils import load_txt_file, parse_txt
            from novel_reader.core.tts import convert_chunk, chunk_to_audio_path, debug_chunk_content

            self.log.emit(f"[DEBUG] Loading book {self.book_id}...")
            book = get_book(self.book_id)
            if book is None:
                self.error.emit("书籍不存在")
                return

            self.log.emit(f"[DEBUG] Book found: {book['title']}")

            # 读取并解析文本
            self.log.emit(f"[DEBUG] Loading and parsing text file: {book['file_path']}")
            text = load_txt_file(book['file_path'])
            chunks, chapters = parse_txt(text)
            self.log.emit(f"[DEBUG] Text parsed: {len(chunks)} chunks, {len(chapters)} chapters")

            # 获取章节列表
            self.log.emit(f"[DEBUG] Loading chapter list...")
            book_chapters = get_book_chapters(self.book_id)
            self.log.emit(f"[DEBUG] Found {len(book_chapters)} chapters in database")

            # 确定转换范围
            if self.start_chunk is not None:
                start_pos = self.start_chunk
            else:
                start_pos = book['current_chunk']

            total = len(chunks)

            # 如果指定了 end_chunk，则只转换到该位置
            if self.end_chunk is not None:
                total = min(total, self.end_chunk)

            converted = 0
            skipped = 0

            self.log.emit(f"[DEBUG] Conversion range: start={start_pos}, end={total}, total_chunks={len(chunks)}")

            # 章节模式：确定当前章节的结束位置
            current_chapter_end = None
            next_chapter_start = None

            if self.chapter_mode and book_chapters:
                self.log.emit(f"[DEBUG] Chapter mode enabled, finding chapter boundaries...")
                # 找到包含 start_pos 的章节
                found_chapter_idx = None
                for i, chapter in enumerate(book_chapters):
                    chapter_start = chapter['start_chunk']
                    # 当前章节的开始位置 <= start_pos < 下一章的开始位置
                    if chapter_start <= start_pos:
                        # 检查是否是包含 start_pos 的章节
                        if i + 1 < len(book_chapters):
                            next_chapter_start_in_loop = book_chapters[i + 1]['start_chunk']
                            if start_pos < next_chapter_start_in_loop:
                                found_chapter_idx = i
                                break
                        else:
                            # 最后一章
                            found_chapter_idx = i
                            break

                if found_chapter_idx is not None:
                    if found_chapter_idx + 1 < len(book_chapters):
                        current_chapter_end = book_chapters[found_chapter_idx + 1]['start_chunk']
                        next_chapter_start = current_chapter_end
                    else:
                        current_chapter_end = total
                        next_chapter_start = None
                    self.log.emit(f"[DEBUG] Chapter {found_chapter_idx}: chunk {start_pos} - {current_chapter_end - 1}")
                else:
                    self.log.emit(f"[DEBUG] Chapter not found for chunk {start_pos}, converting all chunks")

            if self.chapter_mode:
                self.log.emit(f"开始转换当前章节 (chunk {start_pos} - {current_chapter_end - 1 if current_chapter_end else total})")

            # 第一阶段：转换到当前章节结束
            first_phase_end = current_chapter_end if self.chapter_mode else total
            first_chunk_converted = False

            self.log.emit(f"[DEBUG] Starting conversion loop: {start_pos} -> {first_phase_end}")

            for i in range(start_pos, first_phase_end):
                # 检查是否应该停止
                if not self._is_running:
                    self.log.emit("转换已取消")
                    break

                audio_path = chunk_to_audio_path(self.book_id, i)

                # 检查是否已存在
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > MIN_SIZE:
                    self.log.emit(f"[{i+1}/{total}] 跳过 分段 {i}（已存在）")
                    skipped += 1
                else:
                    chunk_text = chunks[i].strip()
                    self.log.emit(f"[{i+1}/{total}] 正在转换 分段 {i}... (文本长度: {len(chunk_text)} 字符)")

                    try:
                        convert_chunk(chunks[i], self.book_id, i)
                        converted += 1
                        self.log.emit(f"[{i+1}/{total}] 转换完成")

                        # 第一个chunk转换完成，发出信号
                        if not first_chunk_converted:
                            # 等待文件完全写入
                            import time
                            max_wait = 5  # 最多等待5秒
                            waited = 0
                            file_ready = False
                            while waited < max_wait:
                                if os.path.exists(audio_path):
                                    file_size = os.path.getsize(audio_path)
                                    if file_size > MIN_SIZE:  # 文件大于20KB认为就绪
                                        file_ready = True
                                        break
                                time.sleep(0.1)
                                waited += 0.1

                            if file_ready:
                                first_chunk_converted = True
                                self.first_chunk_ready.emit(start_pos)
                                self.log.emit(f"✓ 第一个音频已就绪 ({os.path.getsize(audio_path)/1024:.1f} KB)，可以开始播放")
                            else:
                                self.log.emit(f"⚠ 警告: 第一个音频文件未就绪，将稍后重试")
                    except ValueError as e:
                        # 文本为空的情况
                        self.log.emit(f"[{i+1}/{total}] ⚠ {e}")
                        self.log.emit(f"[{i+1}/{total}] 跳过（空文本）")
                        # 为空文本创建一个静音文件，避免播放卡住
                        try:
                            import wave
                            audio_path = chunk_to_audio_path(self.book_id, i)
                            Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
                            with wave.open(str(audio_path), 'wb') as wav_file:
                                wav_file.setnchannels(1)
                                wav_file.setsampwidth(2)
                                wav_file.setframerate(22050)
                                # 写入0.1秒的静音
                                wav_file.writeframes(b'\x00\x00' * 2205)
                            self.log.emit(f"[{i+1}/{total}] 已创建静音文件")
                            converted += 1
                        except Exception as create_error:
                            self.log.emit(f"[{i+1}/{total}] 创建静音文件失败: {create_error}")
                    except Exception as e:
                        self.log.emit(f"[{i+1}/{total}] ❌ 转换失败: {e}")
                        import traceback
                        self.log.emit(f"[{i+1}/{total}] 详细错误:\n{traceback.format_exc()}")

                # 更新进度
                self.progress.emit(i + 1, total)

            # 章节模式：发送当前章节完成信号
            if self.chapter_mode and self._is_running:
                self.log.emit(f"当前章节转换完成！")
                if next_chapter_start is not None:
                    self.chapter_finished.emit(first_phase_end, next_chapter_start)
                else:
                    # 最后一章
                    self.chapter_finished.emit(first_phase_end, None)

            # 第二阶段：继续转换指定数量的后续章节（后台）
            if self.chapter_mode and self._is_running and next_chapter_start is not None:
                # 计算预转换的结束位置
                preview_end_chunk = first_phase_end  # 默认只转换当前章节

                if self.max_preview_chapters > 0:
                    # 找到当前章节的索引
                    current_chapter_idx = -1
                    for i, chapter in enumerate(book_chapters):
                        if chapter['start_chunk'] <= start_pos:
                            current_chapter_idx = i
                        else:
                            break

                    # 计算需要预转换到的章节索引
                    last_preview_chapter_idx = min(
                        current_chapter_idx + self.max_preview_chapters,
                        len(book_chapters) - 1
                    )

                    # 预转换到指定章节的结束位置
                    if last_preview_chapter_idx + 1 < len(book_chapters):
                        preview_end_chunk = book_chapters[last_preview_chapter_idx + 1]['start_chunk']
                    else:
                        preview_end_chunk = total  # 到文件末尾

                    self.log.emit(f"继续预转换后续 {self.max_preview_chapters} 章 (chunk {first_phase_end} - {preview_end_chunk})...")
                else:
                    self.log.emit(f"不预转换后续章节")

                # 只转换到预转换的结束位置
                for i in range(first_phase_end, preview_end_chunk):
                    # 检查是否应该停止
                    if not self._is_running:
                        self.log.emit("转换已取消")
                        break

                    audio_path = chunk_to_audio_path(self.book_id, i)

                    # 检查是否已存在
                    if os.path.exists(audio_path):
                        skipped += 1
                    else:
                        self.log.emit(f"[{i+1}/{total}] 后台转换...")
                        try:
                            convert_chunk(chunks[i], self.book_id, i)
                            converted += 1
                        except Exception as e:
                            self.log.emit(f"[{i+1}/{total}] 转换失败: {e}")

                    # 更新进度
                    self.progress.emit(i + 1, total)

            # 完成
            if self._is_running:
                summary = f"转换完成: {book['title']}\n"
                summary += f"新转换: {converted} 个\n"
                summary += f"已跳过: {skipped} 个\n"
                summary += f"总计: {total} 个"
                self.log.emit(summary)
                self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """停止转换"""
        self._is_running = False
        self.terminate()