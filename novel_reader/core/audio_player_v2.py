"""
音频播放器 - 支持 sounddevice 和 mpv

提供统一的音频播放接口，自动选择最佳后端
"""

import threading
import time
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
    def progress(self) -> float:
        """播放进度百分比"""
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
        import wave

        if not self.sd:
            raise RuntimeError("sounddevice not available")

        # 停止之前的播放
        self.stop()

        # 设置状态和回调
        self.state = PlayerState.PLAYING
        self.on_finished = on_finished
        self.on_progress = on_progress
        self.current_file = audio_path

        # 重置标志
        self._stop_flag.clear()
        self._pause_flag.clear()

        # 启动播放线程
        self._play_thread = threading.Thread(
            target=self._play_audio,
            args=(audio_path, start_offset_ms),
            daemon=True
        )
        self._play_thread.start()

    def _play_audio(self, audio_path: str, start_offset_ms: int):
        """播放音频文件"""
        import wave
        import numpy as np

        try:
            with wave.open(audio_path, 'rb') as wav_file:
                # 获取音频参数
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration_ms = int((frames / rate) * 1000)

                # 计算起始帧
                start_frame = int((start_offset_ms / 1000) * rate)

                # 设置起始位置
                if start_frame > 0:
                    wav_file.setpos(start_frame)

                # 读取数据
                data = wav_file.readframes(frames - start_frame)
                audio_data = np.frombuffer(data, dtype=np.int16)

                # 转换为 float32
                audio_data = audio_data.astype(np.float32) / 32768.0

                # 应用音量
                audio_data = audio_data * self._volume

                # 播放
                self._stream = self.sd.OutputStream(
                    samplerate=rate,
                    channels=1,
                    dtype='float32'
                )

                with self._stream:
                    chunk_size = 1024
                    offset = start_offset_ms

                    for i in range(0, len(audio_data), chunk_size):
                        # 检查停止标志
                        if self._stop_flag.is_set():
                            break

                        # 检查暂停标志
                        while self._pause_flag.is_set():
                            if self._stop_flag.is_set():
                                break
                            time.sleep(0.1)

                        # 播放音频块
                        chunk = audio_data[i:i+chunk_size]
                        self._stream.write(chunk)

                        # 更新进度
                        offset = int((i / rate) * 1000) + start_offset_ms
                        if self.on_progress:
                            self.on_progress(offset, duration_ms)

                    # 播放完成
                    if not self._stop_flag.is_set():
                        if self.on_finished:
                            self.on_finished()

        except Exception as e:
            print(f"[AudioPlayer] Error: {e}")
            self.state = PlayerState.ERROR
        finally:
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
        Seek 到指定位置（需要重新加载音频）

        Args:
            offset_ms: 偏移（毫秒）
        """
        if self.current_file and self.state != PlayerState.STOPPED:
            # 停止当前播放
            self.stop()
            # 重新播放
            self.play(self.current_file, offset_ms,
                     self.on_finished, self.on_progress)

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.state == PlayerState.PAUSED

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量 (0.0 - 1.0)
        """
        self._volume = max(0.0, min(1.0, volume))


# ==================== 简化版播放器（使用 mpv 作为 fallback）====================

class MpvAudioPlayer:
    """
    简化音频播放器 - 使用 mpv

    作为 sounddevice 不可用时的后备方案

    使用 mpv IPC (进程间通信) 进行控制
    """

    def __init__(self, mpv_bin: str = "mpv"):
        """初始化播放器"""
        self.mpv_bin = mpv_bin
        self.process = None
        self.state = PlayerState.STOPPED
        self.current_file: Optional[str] = None

        # IPC socket 路径
        self.ipc_socket_path: Optional[str] = None

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
        import tempfile
        import os

        print(f"[MpvAudioPlayer] DEBUG: play() called with audio_path={audio_path}")

        self.on_finished = on_finished
        self.current_file = audio_path

        # 创建 IPC socket 文件
        if self.ipc_socket_path and os.path.exists(self.ipc_socket_path):
            os.unlink(self.ipc_socket_path)

        fd, self.ipc_socket_path = tempfile.mkstemp(suffix='.sock', prefix='mpv-')
        os.close(fd)
        os.unlink(self.ipc_socket_path)

        cmd = [
            self.mpv_bin,
            "--no-video",
            "--really-quiet",
            f"--input-ipc-server={self.ipc_socket_path}"
        ]
        print(f"[MpvAudioPlayer] DEBUG: cmd={' '.join(cmd)}")

        # 如果有起始偏移
        if start_offset_ms > 0:
            start_sec = start_offset_ms / 1000
            cmd.extend(["--start", str(start_sec)])

        cmd.append(audio_path)

        print(f"[MpvAudioPlayer] DEBUG: Full command: {' '.join(cmd)}")
        print(f"[MpvAudioPlayer] DEBUG: IPC socket: {self.ipc_socket_path}")
        print(f"[MpvAudioPlayer] DEBUG: Starting mpv process...")

        self.process = subprocess.Popen(cmd)
        self.state = PlayerState.PLAYING

        print(f"[MpvAudioPlayer] DEBUG: Process started, PID={self.process.pid}")

        # 启动监控线程
        thread = threading.Thread(
            target=self._monitor,
            daemon=True
        )
        thread.start()
        print(f"[MpvAudioPlayer] DEBUG: Monitor thread started")

    def _send_command(self, *args):
        """
        通过 IPC 发送命令到 mpv

        Args:
            *args: mpv 命令参数，例如 "stop", "set", "pause", "yes"
        """
        import socket
        import json
        import os

        if not self.ipc_socket_path:
            print("[MpvAudioPlayer] Warning: No IPC socket path")
            return False

        if not os.path.exists(self.ipc_socket_path):
            print(f"[MpvAudioPlayer] Warning: IPC socket not exists: {self.ipc_socket_path}")
            return False

        try:
            # 创建 Unix socket 连接
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.ipc_socket_path)

            # 构建 JSON 命令
            command = {"command": list(args)}
            message = json.dumps(command) + "\n"

            # 发送命令
            sock.sendall(message.encode('utf-8'))
            sock.close()

            print(f"[MpvAudioPlayer] IPC command sent: {args}")
            return True

        except Exception as e:
            print(f"[MpvAudioPlayer] IPC command failed: {e}")
            return False

    def _monitor(self):
        """监控播放进程"""
        if self.process:
            self.process.wait()
            # 清理 IPC socket
            if self.ipc_socket_path:
                import os
                try:
                    os.unlink(self.ipc_socket_path)
                except:
                    pass
            if self.on_finished:
                self.on_finished()
            self.state = PlayerState.STOPPED

    def stop(self):
        """停止播放"""
        # 优先使用 IPC 发送停止命令
        if self._send_command("stop"):
            self.state = PlayerState.STOPPED
            print("[MpvAudioPlayer] ⏹ Stopped (via IPC)")
            return

        # 如果 IPC 失败，使用传统方式
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.state = PlayerState.STOPPED

    def pause(self):
        """暂停播放"""
        # 使用 IPC 发送暂停命令
        if self._send_command("set", "pause", "yes"):
            self.state = PlayerState.PAUSED
            print("[MpvAudioPlayer] ⏸ Paused (via IPC)")
        else:
            print("[MpvAudioPlayer] Pause not supported")

    def resume(self):
        """恢复播放"""
        # 使用 IPC 发送恢复命令
        if self._send_command("set", "pause", "no"):
            self.state = PlayerState.PLAYING
            print("[MpvAudioPlayer] ▶ Resumed (via IPC)")
        else:
            print("[MpvAudioPlayer] Resume not supported")

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量 (0.0 - 1.0)
        """
        volume_100 = int(volume * 100)
        self._send_command("set", "volume", volume_100)
        print(f"[MpvAudioPlayer] 🔊 Volume: {volume_100}%")

    @property
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.state == PlayerState.PAUSED

    def get_duration(self, audio_path: str) -> int:
        """获取音频时长"""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return int((frames / rate) * 1000)
        except:
            return 0
