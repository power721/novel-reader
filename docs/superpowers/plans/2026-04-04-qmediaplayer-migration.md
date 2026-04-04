# QMediaPlayer Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace mpv-based audio player with QMediaPlayer in `player.py`, removing external dependency while maintaining full feature parity.

**Architecture:** Create `QtAudioPlayer` class wrapping QMediaPlayer with Qt signals for events. Keep existing module-level API unchanged for zero breaking changes. All module functions delegate to singleton `QtAudioPlayer` instance.

**Tech Stack:** PySide6.QtMultimedia, QMediaPlayer, QAudioOutput, Qt signals/slots

---

## File Structure

**Modified:**
- `novel_reader/core/player.py` - Replace mpv implementation with QMediaPlayer

**Key Changes:**
- Add `QtAudioPlayer` class (QObject with signals)
- Replace subprocess-based `play_audio()` with QMediaPlayer calls
- Remove IPC socket code completely
- Remove mpv subprocess code
- Keep all module-level function signatures unchanged

---

## Task 1: Add QtAudioPlayer Class Skeleton

**Files:**
- Modify: `novel_reader/core/player.py:1-50`

- [ ] **Step 1: Add QtAudioPlayer class with signal definitions**

Add this class at the top of the file, after imports but before the existing configuration section:

```python
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
```

- [ ] **Step 2: Add imports for Qt Multimedia**

At the top of the file, add these imports:

```python
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
```

- [ ] **Step 3: Run the application to verify imports work**

Run: `python -m novel_reader --test`
Expected: Application starts without import errors

- [ ] **Step 4: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: add QtAudioPlayer class skeleton with Qt signals"
```

---

## Task 2: Implement Play Method

**Files:**
- Modify: `novel_reader/core/player.py:QtAudioPlayer.play`

- [ ] **Step 1: Implement the play method**

Add this method to `QtAudioPlayer` class:

```python
def play(self, audio_path: str, start_offset_ms: int = 0):
    """
    Play audio file

    Args:
        audio_path: Path to audio file
        start_offset_ms: Start position in milliseconds
    """
    import os

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

    self._is_playing = True
    self._is_paused = False

    print(f"[QtAudioPlayer] ▶ Playing: {os.path.basename(audio_path)}")
```

- [ ] **Step 2: Implement stop method**

Add this method to `QtAudioPlayer` class:

```python
def stop(self):
    """Stop playback"""
    if self._is_playing or self._is_paused:
        self._media_player.stop()
        self._is_playing = False
        self._is_paused = False
        print("[QtAudioPlayer] ⏹ Stopped")
```

- [ ] **Step 3: Implement pause method**

Add this method to `QtAudioPlayer` class:

```python
def pause(self):
    """Pause playback"""
    if self._is_playing and not self._is_paused:
        self._media_player.pause()
        self._is_paused = True
        print("[QtAudioPlayer] ⏸ Paused")
```

- [ ] **Step 4: Implement resume method**

Add this method to `QtAudioPlayer` class:

```python
def resume(self):
    """Resume playback"""
    if self._is_paused:
        self._media_player.play()
        self._is_paused = False
        print("[QtAudioPlayer] ▶ Resumed")
```

- [ ] **Step 5: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: implement QtAudioPlayer play, stop, pause, resume methods"
```

---

## Task 3: Implement Volume and Speed Controls

**Files:**
- Modify: `novel_reader/core/player.py:QtAudioPlayer`

- [ ] **Step 1: Implement set_volume method**

Add this method to `QtAudioPlayer` class:

```python
def set_volume(self, volume: float):
    """
    Set volume

    Args:
        volume: Volume level (0.0 - 1.0)
    """
    self._volume = max(0.0, min(1.0, volume))
    self._audio_output.setVolume(self._volume)
    print(f"[QtAudioPlayer] 🔊 Volume: {int(self._volume * 100)}%")
```

- [ ] **Step 2: Implement set_playback_speed method**

Add this method to `QtAudioPlayer` class:

```python
def set_playback_speed(self, speed: float):
    """
    Set playback speed

    Args:
        speed: Playback speed (0.5 - 2.0)
    """
    self._playback_speed = max(0.5, min(2.0, speed))
    self._media_player.setPlaybackRate(self._playback_speed)
    print(f"[QtAudioPlayer] ⏱ Speed: {self._playback_speed:.2f}x")
```

- [ ] **Step 3: Implement seek method**

Add this method to `QtAudioPlayer` class:

```python
def seek(self, offset_ms: int):
    """
    Seek to position

    Args:
        offset_ms: Position in milliseconds
    """
    self._media_player.setPosition(offset_ms)
    print(f"[QtAudioPlayer] ⏩ Seek to {offset_ms}ms")
```

- [ ] **Step 4: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: implement QtAudioPlayer volume, speed, and seek controls"
```

---

## Task 4: Create Module-Level Singleton Instance

**Files:**
- Modify: `novel_reader/core/player.py:50-100`

- [ ] **Step 1: Add singleton instance and initialization**

Add after the QtAudioPlayer class definition:

```python
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
```

- [ ] **Step 2: Remove old mpv global variables**

Remove or comment out these old global variables:
- `_playback_state` dictionary
- `_volume` global variable
- `_playback_speed` global variable
- `_ipc_socket` variable

- [ ] **Step 3: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "refactor: add QtAudioPlayer singleton, remove old mpv globals"
```

---

## Task 5: Replace play_audio Function

**Files:**
- Modify: `novel_reader/core/player.py:play_audio`

- [ ] **Step 1: Replace play_audio implementation**

Find the existing `play_audio` function and replace it entirely with:

```python
def play_audio(file_path: str, should_stop_check_fn=None) -> None:
    """
    Play audio file using QMediaPlayer

    Args:
        file_path: Audio file path
        should_stop_check_fn: Optional callback to check if should stop (deprecated, kept for compatibility)

    Raises:
        FileNotFoundError: If audio file not found
    """
    import os

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
        raise FileNotFoundError(f"音频文件过小，已删除: {file_size}")

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
```

- [ ] **Step 2: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace play_audio with QMediaPlayer implementation"
```

---

## Task 6: Replace stop_playback Function

**Files:**
- Modify: `novel_reader/core/player.py:stop_playback`

- [ ] **Step 1: Replace stop_playback implementation**

Find the existing `stop_playback` function and replace it with:

```python
def stop_playback() -> None:
    """Stop current playback"""
    global _player

    if _player:
        _player.stop()
```

- [ ] **Step 2: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace stop_playback with QMediaPlayer implementation"
```

---

## Task 7: Replace pause_mpv and resume_mpv Functions

**Files:**
- Modify: `novel_reader/core/player.py:pause_mpv`

- [ ] **Step 1: Replace pause_mpv implementation**

Find the existing `pause_mpv` function and replace it with:

```python
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
```

- [ ] **Step 2: Replace resume_mpv implementation**

Find the existing `resume_mpv` function and replace it with:

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace pause_mpv/resume_mpv with QMediaPlayer implementation"
```

---

## Task 8: Replace Volume Control Functions

**Files:**
- Modify: `novel_reader/core/player.py:set_volume`

- [ ] **Step 1: Replace set_volume implementation**

Find the existing `set_volume` function and replace it with:

```python
def set_volume(volume: float) -> None:
    """
    Set volume

    Args:
        volume: Volume value (0.0 - 1.0)
    """
    player = _get_player()
    player.set_volume(volume)
```

- [ ] **Step 2: Replace get_volume implementation**

Find the existing `get_volume` function and replace it with:

```python
def get_volume() -> float:
    """
    Get current volume

    Returns:
        Volume value (0.0 - 1.0)
    """
    player = _get_player()
    return player._volume
```

- [ ] **Step 3: Replace adjust_volume implementation**

Find the existing `adjust_volume` function and replace it with:

```python
def adjust_volume(delta: float) -> None:
    """
    Adjust volume

    Args:
        delta: Volume change amount (positive to increase, negative to decrease)
    """
    current = get_volume()
    set_volume(current + delta)
```

- [ ] **Step 4: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace volume control functions with QMediaPlayer implementation"
```

---

## Task 9: Replace Playback Speed Functions

**Files:**
- Modify: `novel_reader/core/player.py:set_playback_speed`

- [ ] **Step 1: Replace set_playback_speed implementation**

Find the existing `set_playback_speed` function and replace it with:

```python
def set_playback_speed(speed: float) -> None:
    """
    Set playback speed

    Args:
        speed: Playback speed (0.5 - 2.0, 1.0 is normal speed)
    """
    player = _get_player()
    player.set_playback_speed(speed)
```

- [ ] **Step 2: Replace get_playback_speed implementation**

Find the existing `get_playback_speed` function and replace it with:

```python
def get_playback_speed() -> float:
    """
    Get current playback speed

    Returns:
        Playback speed (0.5 - 2.0)
    """
    player = _get_player()
    return player._playback_speed
```

- [ ] **Step 3: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace playback speed functions with QMediaPlayer implementation"
```

---

## Task 10: Replace Real-time Control Functions

**Files:**
- Modify: `novel_reader/core/player.py:set_playback_speed_realtime`

- [ ] **Step 1: Replace set_playback_speed_realtime implementation**

Find the existing `set_playback_speed_realtime` function and replace it with:

```python
def set_playback_speed_realtime(speed: float) -> None:
    """
    Set playback speed in real-time (during playback)

    Args:
        speed: Playback speed (0.5 - 2.0)
    """
    player = _get_player()
    player.set_playback_speed(speed)
```

- [ ] **Step 2: Replace set_volume_realtime implementation**

Find the existing `set_volume_realtime` function and replace it with:

```python
def set_volume_realtime(volume: float) -> None:
    """
    Set volume in real-time (during playback)

    Args:
        volume: Volume value (0.0 - 1.0)
    """
    player = _get_player()
    player.set_volume(volume)
```

- [ ] **Step 3: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "feat: replace real-time control functions with QMediaPlayer implementation"
```

---

## Task 11: Remove IPC and MPV-Specific Code

**Files:**
- Modify: `novel_reader/core/player.py:check_mpv_installed`

- [ ] **Step 1: Remove or replace check_mpv_installed**

Replace the function with:

```python
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
```

- [ ] **Step 2: Remove all IPC socket related code**

Remove any remaining code related to:
- IPC socket path variables
- Socket connections
- IPC command sending

- [ ] **Step 3: Remove MPV_BIN constant**

Remove the `MPV_BIN = "mpv"` constant

- [ ] **Step 4: Commit**

```bash
git add novel_reader/core/player.py
git commit -m "refactor: remove IPC socket and mpv-specific code"
```

---

## Task 12: Keep Unchanged Functions

**Files:**
- Verify: `novel_reader/core/player.py:update_progress`

- [ ] **Step 1: Verify these functions remain unchanged**

Ensure these functions are NOT modified (they don't interact with mpv):
- `update_progress()`
- `get_progress()`
- `reset_progress()`
- `play_book()`
- `play_chunk()`
- `diagnose_audio_files()`
- `print_diagnosis()`
- `delete_corrupted_audio()`

- [ ] **Step 2: Verify play_book and play_chunk still work**

These functions call `play_audio()` internally, so they should work with the new implementation.

- [ ] **Step 3: Commit if any minor adjustments needed**

```bash
git add novel_reader/core/player.py
git commit -m "refactor: ensure non-mpv functions remain unchanged"
```

---

## Task 13: Manual Testing

**Files:**
- Test: `novel_reader/gui/pyside_main.py`

- [ ] **Step 1: Start the application**

Run: `python -m novel_reader --test`
Expected: Application starts without errors

- [ ] **Step 2: Import a test book**

Create a test book and import it through the GUI

- [ ] **Step 3: Convert chapters to audio**

Use the GUI to convert some chapters to audio

- [ ] **Step 4: Play audio**

Click play button and verify audio plays

- [ ] **Step 5: Test pause/resume**

Pause playback, then resume - verify it works

- [ ] **Step 6: Test stop**

Stop playback - verify it stops cleanly

- [ ] **Step 7: Test volume control**

Adjust volume during playback - verify it changes in real-time

- [ ] **Step 8: Test playback speed**

Change playback speed - verify it changes in real-time

- [ ] **Step 9: Test chapter navigation**

Play through multiple chapters - verify smooth transitions

- [ ] **Step 10: Test error handling**

Try playing a non-existent file - verify graceful error handling

- [ ] **Step 11: Commit any bug fixes**

```bash
git add novel_reader/core/player.py
git commit -m "fix: address issues found during manual testing"
```

---

## Task 14: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md architecture section**

Update the architecture documentation to reflect QMediaPlayer instead of mpv:

Find the section about audio playback and update it to mention QMediaPlayer.

- [ ] **Step 2: Update dependencies section**

Remove mpv from system dependencies, add PySide6.QtMultimedia note

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update architecture documentation for QMediaPlayer"
```

---

## Task 15: Final Cleanup and Verification

**Files:**
- Verify: `novel_reader/core/player.py`

- [ ] **Step 1: Search for any remaining mpv references**

Run: `grep -n "mpv\|ipc\|socket" novel_reader/core/player.py`
Expected: Only in comments or string literals describing what changed

- [ ] **Step 2: Search for subprocess references**

Run: `grep -n "subprocess\|Popen" novel_reader/core/player.py`
Expected: Only in other unrelated functions

- [ ] **Step 3: Verify all imports are needed**

Check that all imports at the top of the file are actually used

- [ ] **Step 4: Run full application test**

Run: `python -m novel_reader`
Expected: Full application works without mpv dependency

- [ ] **Step 5: Final commit**

```bash
git add novel_reader/core/player.py CLAUDE.md
git commit -m "feat: complete QMediaPlayer migration - mpv dependency removed"
```

---

## Testing Checklist

After implementation, verify:

- [ ] Application starts without mpv installed
- [ ] Can play single audio file
- [ ] Can play full book (multiple chunks)
- [ ] Pause/resume works during playback
- [ ] Stop works during playback
- [ ] Volume adjustment works in real-time
- [ ] Playback speed adjustment works in real-time
- [ ] Chapter transitions work smoothly
- [ ] Error handling for missing files works
- [ ] Progress tracking still works
- [ ] No console errors or warnings

---

## Notes

- **No breaking changes:** All existing function signatures are preserved
- **Thread safety:** Qt signals/slots handle thread safety automatically
- **No external dependencies:** mpv is no longer required
- **Cross-platform:** QMediaPlayer works on Windows, Linux, macOS
