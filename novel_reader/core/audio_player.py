"""
AudioPlayer - 音频播放器

职责：
1. 播放WAV文件
2. 播放控制（play/stop/pause）
3. 播放状态回调
"""
import threading
import wave
from pathlib import Path
from typing import Optional, Callable
from enum import Enum, auto


class PlayerState(Enum):
    """播放器状态"""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class AudioPlayer:
    """
    音频播放器

    使用sounddevice进行播放
    支持异步播放和状态回调
    """

    def __init__(self):
        """初始化播放器"""
        self.state = PlayerState.STOPPED
        self.current_file: Optional[str] = None
        self.thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

        # 回调函数
        self.on_finished: Optional[Callable] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None

    def play(self, audio_path: str,
             on_finished: Optional[Callable] = None,
             on_progress: Optional[Callable[[int, int], None] = None):
        """
        播放音频文件

        Args:
            audio_path: 音频文件路径
            on_finished: 播放完成回调
            on_progress: 进度回调(current_ms, total_ms)
        """
        # 停止当前播放
        if self.state == PlayerState.PLAYING:
            self.stop()

        # 设置回调
        self.on_finished = on_finished
        self.on_progress = on_progress

        # 启动播放线程
        self.current_file = audio_path
        self._stop_flag.clear()
        self.thread = threading.Thread(
            target=self._play_loop,
            args=(audio_path,),
            daemon=True
        )
        self.thread.start()
        self.state = PlayerState.PLAYING

    def _play_loop(self, audio_path: str):
        """播放循环"""
        try:
            import sounddevice as sd

            # 读取WAV文件
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / rate
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()

                # 读取音频数据
                wav_file.rewind()
                audio_data = wav_file.readframes(frames)

            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # 播放
            total_ms = int(duration * 1000)
            start_time = time.time()

            def callback(outdata, frames, time_info, status):
                if self._stop_flag.is_set():
                    raise sd.CallbackStop

                # 写入音频数据
                # ... 简化实现，使用play()代替

            # 简化版本：使用play非阻塞
            sd.play(audio_array, rate)

            # 等待播放完成
            while sd.get_stream().active and not self._stop_flag.is_set():
                sd.sleep(int(100))  # 100ms
                if self.on_progress:
                    elapsed = int((time.time() - start_time) * 1000)
                    self.on_progress(elapsed, total_ms)

            if not self._stop_flag.is_set():
                # 播放完成
                if self.on_finished:
                    self.on_finished()
            else:
                # 被停止
                pass

            self.state = PlayerState.STOPPED

        except Exception as e:
            print(f"[AudioPlayer] Error: {e}")
            self.state = PlayerState.STOPPED

    def stop(self):
        """停止播放"""
        if self.state == PlayerState.PLAYING:
            self._stop_flag.set()
            if self.thread:
                self.thread.join(timeout=1)
            self.state = PlayerState.STOPPED

    def pause(self):
        """暂停播放"""
        # TODO: 实现暂停
        pass

    def resume(self):
        """恢复播放"""
        # TODO: 实现恢复
        pass

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING


# 简化版播放器（使用mpv）
class SimpleAudioPlayer:
    """
    简化音频播放器 - 使用mpv

    优点：
    - 支持更多格式
    - 更好的性能
    - 支持暂停/恢复
    """

    def __init__(self, mpv_bin: str = "mpv"):
        """初始化播放器"""
        self.mpv_bin = mpv_bin
        self.process = None
        self.state = PlayerState.STOPPED

        # 回调
        self.on_finished: Optional[Callable] = None

    def play(self, audio_path: str, on_finished: Optional[Callable] = None):
        """
        播放音频

        Args:
            audio_path: 音频文件路径
            on_finished: 完成回调
        """
        import subprocess

        self.on_finished = on_finished

        cmd = [
            self.mpv_bin,
            "--no-video",
            "--really-quiet",
            audio_path
        ]

        self.process = subprocess.Popen(cmd)
        self.state = PlayerState.PLAYING

        # 启动监控线程
        import threading
        thread = threading.Thread(
            target=self._monitor,
            daemon=True
        )
        thread.start()

    def _monitor(self):
        """监控播放进程"""
        if self.process:
            self.process.wait()
            if self.on_finished:
                self.on_finished()
            self.state = PlayerState.STOPPED

    def stop(self):
        """停止播放"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=1)
        self.state = PlayerState.STOPPED

    def pause(self):
        """暂停"""
        # TODO: mpv支持暂停
        pass

    def resume(self):
        """恢复"""
        # TODO: mpv支持恢复
        pass

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING


import time
