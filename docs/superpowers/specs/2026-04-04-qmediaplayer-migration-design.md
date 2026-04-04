# QMediaPlayer Migration Design

**Date:** 2026-04-04
**Author:** Claude (Harold)
**Status:** Approved

## Overview

Replace the mpv-based audio player in `player.py` with QMediaPlayer (Qt Multimedia framework). This removes the external mpv dependency, improves Qt integration, and provides cross-platform consistency.

**Scope:** Replace v1 player only (`player.py`). Keep v2 architecture unchanged.

## Motivation

1. **Remove external dependency** - Eliminate need for users to install mpv separately
2. **Better Qt integration** - Native Qt multimedia that integrates better with PySide6
3. **Cross-platform consistency** - More consistent behavior across Windows/Linux/macOS
4. **No IPC complexity** - QMediaPlayer runs in-process, eliminating socket communication

## Architecture

### Current State (mpv subprocess)

```
PlaybackWorker → player.py functions → mpv subprocess → OS audio
                    ↓
              IPC socket (for pause/resume/volume)
```

### New State (QMediaPlayer)

```
PlaybackWorker → player.py functions → QtAudioPlayer → QMediaPlayer → OS audio
                                                ↓
                                          Qt signals (for events)
```

### Key Changes

- **No subprocesses** - QMediaPlayer runs in the same process
- **No IPC** - Direct method calls instead of socket communication
- **Qt signals** - Use QMediaPlayer's built-in signals for playback events
- **Singleton pattern** - Single `QtAudioPlayer` instance managed by the module

### Thread Model

- QMediaPlayer must run in the GUI thread (Qt requirement)
- `PlaybackWorker` runs in a background thread
- Communication via Qt's signal/slot mechanism (thread-safe by default)

## Components

### QtAudioPlayer Class

New class that wraps QMediaPlayer with the application's needed functionality:

```python
class QtAudioPlayer(QObject):
    """QMediaPlayer wrapper for audiobook playback"""

    # Signals
    finished = Signal()  # Playback completed
    error = Signal(str)  # Playback error
    position_changed = Signal(int, int)  # current_ms, total_ms

    # Core methods
    def play(self, audio_path: str, start_offset_ms: int = 0)
    def stop()
    def pause()
    def resume()
    def seek(self, offset_ms: int)
    def set_volume(self, volume: float)  # 0.0 - 1.0
    def set_playback_speed(self, speed: float)  # 0.5 - 2.0

    # Properties
    @property
    def is_playing(self) -> bool

    @property
    def is_paused(self) -> bool
```

**Key Design Decisions:**
- Inherits from `QObject` to support signals/slots
- Manages QMediaPlayer and QAudioOutput lifecycle
- Handles all Qt multimedia setup and teardown
- Thread-safe: methods can be called from any thread

### Module-level API (unchanged)

All existing functions in `player.py` keep the same signatures:

- `play_audio(file_path, should_stop_check_fn)` → delegates to QtAudioPlayer
- `stop_playback()` → delegates to QtAudioPlayer
- `pause_mpv()` / `resume_mpv()` → delegates to QtAudioPlayer
- `set_volume()` / `set_playback_speed()` → real-time adjustments
- `set_volume_realtime()` / `set_playback_speed_realtime()` → real-time adjustments
- All other functions remain unchanged (`update_progress`, `get_progress`, etc.)

**Singleton Instance:**
- Module maintains a single `_player: QtAudioPlayer` instance
- All module functions use this instance
- Initialized on first use

## Implementation Details

### Playback Flow

**Current mpv flow:**
```python
def play_audio(file_path, should_stop_check_fn):
    cmd = [MPV_BIN, "--no-video", "--really-quiet", ..., file_path]
    process = subprocess.Popen(cmd)
    while process.poll() is None:
        if should_stop_check_fn():
            process.terminate()
            break
        time.sleep(0.1)
```

**New QMediaPlayer flow:**
```python
class QtAudioPlayer:
    def play(self, audio_path: str, start_offset_ms: int = 0):
        self._media_player.setSource(QUrl.fromLocalFile(audio_path))
        self._audio_output.setVolume(self._volume)
        self._media_player.play()

        # Handle start offset
        if start_offset_ms > 0:
            self._media_player.setPosition(start_offset_ms)

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.finished.emit()
```

**Key Implementation Notes:**
1. **Stop checking**: Instead of polling `should_stop_check_fn`, PlaybackWorker calls `stop()` directly
2. **Position tracking**: Connect to `positionChanged` signal for progress updates
3. **Error handling**: Connect to `errorOccurred` signal
4. **Threading**: QMediaPlayer automatically handles threading via Qt event loop

### Real-time Control

All real-time controls become direct method calls (no IPC):

```python
def set_volume_realtime(volume: float):
    _player.set_volume(volume)  # Direct call, no IPC

def set_playback_speed_realtime(speed: float):
    _player.set_playback_speed(speed)  # Direct call

def pause_mpv():
    _player.pause()  # Direct call

def resume_mpv():
    _player.resume()  # Direct call
```

### Migration Strategy

1. Keep `player.py` structure intact
2. Add `QtAudioPlayer` class at the top of the file
3. Replace mpv-specific code with QMediaPlayer calls
4. Remove IPC socket code (no longer needed)
5. Remove subprocess code (no longer needed)
6. Add fallback: if QMediaPlayer unavailable, show error (not fallback to mpv)

### Dependencies

**Remove:**
- No more mpv system dependency
- No more IPC socket handling

**Keep:**
- PySide6 (already required)
- All other dependencies unchanged

**Add:**
- PySide6.QtMultimedia (part of PySide6)

## Error Handling

### QMediaPlayer Errors

- Connect to `errorOccurred` signal
- Emit `error` signal with error message
- PlaybackWorker already handles `error` signal

### Missing Audio Files

- Keep existing validation (file exists, size > 5KB)
- QMediaPlayer will emit error if file is invalid
- Same retry logic as current implementation

### Unsupported Formats

- QMediaPlayer supports MP3, WAV, M4A, OGG, etc.
- Edge TTS outputs MP3, which is fully supported
- No format conversion needed

### Edge Cases

**Stop During Playback:**
- Current: Poll `should_stop_check_fn()` in loop
- New: Direct `player.stop()` call from PlaybackWorker

**Pause During Playback:**
- Current: IPC socket to mpv
- New: Direct `player.pause()` call

**Seek During Playback:**
- Current: Not supported in current implementation
- New: Can add if needed via `player.seek(offset_ms)`

**Thread Safety:**
- QMediaPlayer methods are thread-safe when called from any thread
- Qt automatically marshals calls to the GUI thread

## Testing Strategy

### Manual Testing Checklist

1. Play single audio file
2. Play full book (multiple chunks)
3. Pause/resume during playback
4. Stop during playback
5. Adjust volume during playback
6. Adjust playback speed during playback
7. Skip chunks (meaningless chunks)
8. Handle missing/corrupted audio files
9. Verify cross-platform behavior (Linux, Windows, macOS)

### No Automated Tests

- Project doesn't have pytest configured yet
- Manual testing matches current project practices

## Files to Modify

- `novel_reader/core/player.py` - Complete rewrite of mpv implementation

## Files Unchanged

- `novel_reader/core/audio_player_v2.py` - Keep as-is
- `novel_reader/gui/workers/playback_worker.py` - No changes needed
- All other files - No changes needed

## Success Criteria

1. ✓ No external mpv dependency required
2. ✓ All current features work (play, stop, pause, resume, volume, speed)
3. ✓ Zero breaking changes to existing code
4. ✓ Cross-platform compatibility
5. ✓ Better Qt integration
6. ✓ No IPC complexity

## Risks & Mitigations

### Risk: QMediaPlayer not available on some systems

**Mitigation:** PySide6.QtMultimedia is part of standard PySide6 installation. If unavailable, show clear error message.

### Risk: Different behavior across platforms

**Mitigation:** QMediaPlayer is designed for cross-platform consistency. Test on multiple platforms.

### Risk: Threading issues

**Mitigation:** Qt's signal/slot mechanism is thread-safe by default. QMediaPlayer handles GUI thread marshalling automatically.

## Timeline Estimate

- Implementation: 2-3 hours
- Testing: 1 hour
- Total: 3-4 hours

## Future Considerations

After this migration:
- Consider integrating v2 architecture with QMediaPlayer
- Add seek functionality if needed
- Explore QMediaPlayer's playlist features for smoother chapter transitions
