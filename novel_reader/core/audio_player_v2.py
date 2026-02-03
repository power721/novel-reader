from __future__ import annotations

"""
AudioPlayer - 基于 sounddevice 的音频播放器

Production级实现：
- 使用 sounddevice 进行低延迟播放
- 支持 play / pause / stop / seek
- 精确的播放进度追踪
- 播放完成回调
- 线程安全
"""
import threading
import time
import wave
import numpy as np
from pathlib import Path
from typing import Optional, Callable, Tuple
from enum import Enum, auto
from dataclasses import dataclass


class PlayerState(Enum):
    """播放器状态"""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    ERROR = auto()


@dataclass
class PlaybackPosition:
    """播放位置"""
    chunk_id: int
    offset_ms: int
    total_ms: int

    @property
    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_ms == 0:
            return 0.0
        return (self.offset_ms / self.total_ms) * 100


class AudioPlayer:
    """
    音频播放器 - 使用 sounddevice

    特性：
    - 低延迟播放
    - 精确进度追踪
    - pause/resume/seek 支持
    - 线程安全
    """

    def __init__(self, sample_rate: int = 22050):
        """
        初始化播放器

        Args:
            sample_rate: 采样率
        """
        self.sample_rate = sample_rate
        self.state = PlayerState.STOPPED
        self._volume = 1.0  # 音量 (0.0 - 1.0)

        # 播放控制
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._play_thread: Optional[threading.Thread] = None

        # 当前播放信息
        self.current_file: Optional[str] = None
        self.current_position: Optional[PlaybackPosition] = None

        # 回调函数
        self.on_finished: Optional[Callable] = None
        self.on_progress: Optional[Callable[[int, int], None]] = None  # (current_ms, total_ms)

        # sounddevice
        self._stream = None
        try:
            import sounddevice as sd
            self.sd = sd
        except ImportError:
            self.sd = None
            print("[AudioPlayer] WARNING: sounddevice not installed, pip install sounddevice")

    def play(self, audio_path: str,
             start_offset_ms: int = 0,
             on_finished: Optional[Callable] = None,
             on_progress: Optional[Callable[[int, int], None]] = None):
        """
        播放音频文件

        Args:
            audio_path: 音频文件路径
            start_offset_ms: 起始偏移（毫秒）
            on_finished: 播放完成回调
            on_progress: 进度回调 (current_ms, total_ms)
        """
        if not self.sd:
            raise RuntimeError("sounddevice not installed")

        # 停止当前播放
        if self.state == PlayerState.PLAYING:
            self.stop()

        # 检查文件
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 读取音频文件
        audio_data, duration_ms = self._load_wav(audio_path)

        # 计算起始位置
        start_sample = int((start_offset_ms / 1000) * self.sample_rate)

        if start_sample >= len(audio_data):
            raise ValueError(f"Start offset ({start_offset_ms}ms) exceeds duration ({duration_ms}ms)")

        # 设置状态
        self.current_file = audio_path
        self.on_finished = on_finished
        self.on_progress = on_progress
        self.state = PlayerState.PLAYING

        # 启动播放线程
        self._stop_flag.clear()
        self._pause_flag.clear()

        self._play_thread = threading.Thread(
            target=self._play_loop,
            args=(audio_data[start_sample:], duration_ms - start_offset_ms),
            daemon=True
        )
        self._play_thread.start()

    def _play_loop(self, audio_data: np.ndarray, duration_ms: int):
        """
        播放循环

        Args:
            audio_data: 音频数据 (numpy array)
            duration_ms: 时长（毫秒）
        """
        try:
            # 创建音频流
            self._stream = self.sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            self._stream.start()

            # 播放参数
            chunk_size = 1024
            total_samples = len(audio_data)
            played_samples = 0
            start_time = time.time()

            # 播放循环
            while played_samples < total_samples:
                # 检查停止标志
                if self._stop_flag.is_set():
                    break

                # 检查暂停标志
                if self._pause_flag.is_set():
                    time.sleep(0.1)
                    continue

                # 计算本次播放的样本数
                remaining = total_samples - played_samples
                samples_to_play = min(chunk_size, remaining)

                # 应用音量控制
                chunk_data = audio_data[played_samples:played_samples + samples_to_play].astype(np.float32)
                chunk_data = chunk_data * self._volume
                chunk_data = np.clip(chunk_data, -32768, 32767).astype(np.int16)
                
                # 播放
                self._stream.write(chunk_data)
                played_samples += samples_to_play

                # 进度回调
                if self.on_progress:
                    current_ms = int((played_samples / self.sample_rate) * 1000)
                    self.on_progress(current_ms, duration_ms)

        except Exception as e:
            print(f"[AudioPlayer] Playback error: {e}")
            self.state = PlayerState.ERROR
        finally:
            # 清理
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            # 更新状态
            if not self._stop_flag.is_set():
                self.state = PlayerState.STOPPED
                if self.on_finished:
                    self.on_finished()
            else:
                self.state = PlayerState.STOPPED

    def stop(self):
        """停止播放"""
        if self.state == PlayerState.PLAYING:
            self._stop_flag.set()
            if self._play_thread:
                self._play_thread.join(timeout=2)
            self.state = PlayerState.STOPPED
            print("[AudioPlayer] ⏹ Stopped")

    def pause(self):
        """暂停播放"""
        if self.state == PlayerState.PLAYING:
            self._pause_flag.set()
            if self._stream:
                self._stream.stop()
            self.state = PlayerState.PAUSED
            print("[AudioPlayer] ⏸ Paused")

    def resume(self):
        """恢复播放"""
        if self.state == PlayerState.PAUSED:
            self._pause_flag.clear()
            if self._stream:
                self._stream.start()
            self.state = PlayerState.PLAYING
            print("[AudioPlayer] ▶ Resumed")

    def seek(self, offset_ms: int):
        """
        Seek到指定位置（需要重新加载音频）

        Args:
            offset_ms: 偏移（毫秒）
        """
        if not self.current_file:
            return

        # 停止当前播放
        was_playing = self.state == PlayerState.PLAYING
        self.stop()

        # 从新位置开始播放
        self.play(
            self.current_file,
            start_offset_ms=offset_ms,
            on_finished=self.on_finished,
            on_progress=self.on_progress
        )

        if not was_playing:
            self.pause()

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.state == PlayerState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.state == PlayerState.STOPPED

    def _load_wav(self, audio_path: str) -> tuple:
        """
        加载WAV文件

        Args:
            audio_path: 音频文件路径

        Returns:
            (audio_data, duration_ms)
        """
        with wave.open(audio_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()

            # 读取音频数据
            audio_data = wav_file.readframes(frames)

        # 转换为numpy数组
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # 如果是立体声，转换为单声道
        if channels == 2:
            audio_array = audio_array.reshape(-1, 2).mean(axis=1).astype(np.int16)

        # 计算时长
        duration_ms = int((frames / rate) * 1000)

        return audio_array, duration_ms

    def get_duration(self, audio_path: str) -> int:
        """
        获取音频文件时长

        Args:
            audio_path: 音频文件路径

        Returns:
            时长（毫秒）
        """
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return int((frames / rate) * 1000)
        except:
            return 0

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量值 (0.0 - 1.0)
        """
        self._volume = max(0.0, min(1.0, volume))
        print(f"[AudioPlayer] Volume set to {self._volume * 100:.0f}%")

    def get_volume(self) -> float:
        """
        获取当前音量

        Returns:
            音量值 (0.0 - 1.0)
        """
        return self._volume

    def adjust_volume(self, delta: float):
        """
        调整音量

        Args:
            delta: 音量变化量 (正数增大，负数减小)
        """
        self.set_volume(self._volume + delta)

    @property
    def volume(self) -> float:
        """当前音量 (只读属性)"""
        return self._volume

    @volume.setter
    def volume(self, value: float):
        """设置音量"""
        self.set_volume(value)


# 简化版播放器（使用mpv作为fallback）
class MpvAudioPlayer:
    """
    简化音频播放器 - 使用 mpv

    作为 sounddevice 不可用时的后备方案
    """

    def __init__(self, mpv_bin: str = "mpv"):
        """初始化播放器"""
        self.mpv_bin = mpv_bin
        self.process = None
        self.state = PlayerState.STOPPED
        self.current_file: Optional[str] = None

        # 回调
        self.on_finished: Optional[Callable] = None

    def play(self, audio_path: str,
             start_offset_ms: int = 0,
             on_finished: Optional[Callable] = None,
             on_progress: Optional[Callable[[int, int], None]] = None):
        """
        播放音频

        Args:
            audio_path: 音频文件路径
            start_offset_ms: 起始偏移（毫秒）
            on_finished: 完成回调
            on_progress: 进度回调
        """
        import subprocess

        self.on_finished = on_finished
        self.current_file = audio_path

        cmd = [self.mpv_bin, "--no-video", "--really-quiet"]

        # 如果有起始偏移
        if start_offset_ms > 0:
            start_sec = start_offset_ms / 1000
            cmd.extend(["--start", str(start_sec)])

        cmd.append(audio_path)

        self.process = subprocess.Popen(cmd)
        self.state = PlayerState.PLAYING

        # 启动监控线程
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
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.state = PlayerState.STOPPED

    def pause(self):
        """暂停（mpv不支持）"""
        print("[MpvAudioPlayer] Pause not supported")

    def resume(self):
        """恢复（mpv不支持）"""
        print("[MpvAudioPlayer] Resume not supported")

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING

    def get_duration(self, audio_path: str) -> int:
        """获取音频时长"""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return int((frames / rate) * 1000)
        except:
            return 0
