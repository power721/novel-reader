# Agent Guidelines for Novel Reader

This file provides guidance for AI agents working on the Novel Reader codebase.

## Build and Test Commands

```bash
# Run the GUI application
python -m novel_reader              # Start PySide6 GUI
python -m novel_reader --test       # Start GUI with test data

# Code formatting (black not currently configured, install manually if needed)
pip install black
black novel_reader/                 # Format code

# Run tests (pytest not yet configured)
python -m pytest tests/             # Run tests (not set up yet)
```

**Note:** No formal testing framework is currently configured. Manual testing with debug prints is used.

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local imports
- Use `from __future__ import annotations` in v2 core modules for forward references
- Use `__all__` to explicitly export public API in `__init__.py` files
- Group related imports with parentheses for multi-line imports

Example:
```python
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from novel_reader.utils import parse_txt, load_txt_file
from novel_reader.models import get_conn
```

### Type Hints
- Use type hints for all function signatures
- Prefer `Optional[T]` over `T | None` for compatibility
- Use `dataclass` for data models with `@property` for computed attributes

### Naming Conventions
- **Classes:** PascalCase (`PlayerWidget`, `AudioPlayer`, `PlaybackController`)
- **Functions/Variables:** snake_case (`import_book`, `get_book`, `set_volume`)
- **Constants:** UPPER_SNAKE_CASE (`AUDIO_DIR`, `MPV_BIN`, `_volume`)
- **Private members:** `_leading_underscore` (`_setup_ui`, `_volume`)
- **Signals:** PascalCase (Qt convention: `play_requested`, `volume_changed`)

### File Structure
- Docstring at top of every file describing module purpose
- Classes use docstrings with triple quotes
- Functions include Args and Returns in docstrings
- Use Chinese comments and docstrings for UI-facing strings

### Error Handling
- Raise specific exceptions (`FileNotFoundError`, `ValueError`)
- Use `try/except` for I/O operations and external dependencies
- Print error messages to console for debugging
- Return `False` or `None` for non-critical failures

Example:
```python
try:
    result = some_operation()
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
    return None
except Exception as e:
    print(f"操作失败: {e}")
    return False
```

### Architecture Guidelines
- **Prefer v2 architecture** over v1 when working on core features
- Core v2 modules: `models_v2.py`, `playback_controller_v2.py`, `audio_player_v2.py`, etc.
- Use chunk-based architecture (~100 chars per chunk)
- Thread-safe operations for TTS and playback
- Use signal/slot pattern for Qt GUI components

### GUI Development (PySide6)
- Widgets inherit from `QWidget` or appropriate Qt classes
- Define signals as class attributes before `__init__`
- Use `@Slot()` decorator for signal handlers
- Separate UI setup in `_setup_ui()` method
- Use Chinese labels for user-facing text

### Constants and Configuration
- Configuration in `novel_reader/core/settings.py` with `DEFAULT_SETTINGS`
- Use `get_setting(key, default)` and `set_setting(key, value)`
- Global constants at module level (e.g., `AUDIO_DIR`, `MPV_BIN`)

### Data Storage
- SQLite database for persistent data
- Settings in `~/.config/novel-reader/config.json`
- Audio files in `~/.local/share/novel-reader/audio/`
- Use `from novel_reader.models import get_conn` for database access

### When to Commit
- Only commit when explicitly requested by the user
- Use descriptive commit messages in Chinese for this project
- Example: `"添加音量调节功能"` or `"修复播放进度保存问题"`

### Important Notes
- TTS uses piper-tts (offline) or Coqui XTTS (online, optional)
- Audio playback via mpv system dependency
- The `ui/` directory contains legacy TUI, prefer GUI changes
- `tests/` directory exists but pytest is not configured
- Use chunk-based navigation for granular seeking
- Volume changes should save to settings immediately
