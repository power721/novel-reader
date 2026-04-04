# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Novel Reader is a local audiobook management system written in Python. It converts text files into audiobooks using Edge TTS (Microsoft neural voices) and plays them using QMediaPlayer. The system uses a chunk-based architecture with intelligent caching and priority-based TTS scheduling for seamless playback.

## Common Commands

### Running the Application
```bash
python -m novel_reader              # Start PySide6 GUI
python -m novel_reader --test       # Start GUI with test data
```

### Testing
```bash
python -m pytest tests/             # Run tests (pytest not yet configured)
```

### Code Quality
```bash
black novel_reader/                 # Format code (not currently configured)
```

## Architecture

### Entry Points
- **GUI**: `novel_reader/gui/pyside_main.py` - Main PySide6 application
- **TUI**: `novel_reader/ui/tui.py` - Legacy Textual terminal UI

### Core Architecture (v2)

The application is being refactored to a modular architecture with these key components:

```
novel_reader/core/
├── models_v2.py              # Data models (TextChunk, Chapter, Book, PlaybackState)
├── playback_controller_v2.py # Central state machine and coordinator
├── chunk_manager_v2.py       # Text parsing and chunking
├── tts_scheduler_v2.py       # Priority-based TTS scheduling
├── audio_cache.py            # LRU cache for audio files
├── audio_player_v2.py        # QMediaPlayer wrapper (legacy)
└── sentence_manager.py       # Sentence-level processing
```

### Key Architectural Patterns

**1. Chunk-based Architecture**
- TextChunk is the minimal logical unit (~100 characters)
- Each chunk has independent state tracking (ready/converting/error)
- Chapters contain multiple chunks for smart navigation
- Audio files are cached per-chunk

**2. Priority-based TTS Scheduling**
- Four priority levels: URGENT > HIGH > NORMAL > LOW
- Current chunk gets highest priority for fast first-sound
- Background worker threads continuously synthesize upcoming chunks
- Auto cache cleanup for invalid files

**3. State Management**
- `PlaybackState` enum defines player states (IDLE, LOADING, READY, PLAYING, PAUSED)
- Controller coordinates TTS scheduling and playback
- Progress persisted across sessions via bookmarks

**4. Thread Model**
```
Main Thread (UI)
    ↓
PlaybackController (logic coordinator)
    ↓
    ├─→ TTS Worker Thread (background synthesis)
    └─→ Audio Player Thread (QMediaPlayer playback)
```

### GUI Structure

```
novel_reader/gui/
├── main_window.py         # MainWindow class
├── pyside_main.py         # Application entry point
├── widgets/               # Custom UI components
│   ├── BookListWidget
│   ├── ChapterListWidget
│   ├── PlayerWidget
│   ├── PlayTextWidget
│   └── TTSWidget
├── workers/               # Background threads
│   ├── PlaybackWorker
│   └── TTSWorker
├── dialogs/
└── controllers/
    └── playback_controller_adapter.py  # Adapts v2 controller to GUI
```

### Data Flow

```
Text File → ChunkManager → TextChunk[]
                              ↓
                         TTSScheduler (priority queue)
                              ↓
                         AudioCache (LRU) ← Edge TTS
                              ↓
                         QtAudioPlayer (QMediaPlayer) → Speakers
```

## Configuration

### Default Parameters (AUDIOBOOK_CONFIG)
```python
{
    "text_chunk_size": 100,        # ~100 characters per chunk
    "tts_batch_chunks": 3,         # Process 3 chunks per batch
    "prefetch_chunks": 2,          # Prefetch 2 chunks ahead
    "audio_cache_size": 80,        # Cache up to 80 chunks
    "max_tts_queue": 5,            # Max 5 TTS tasks in queue
    "first_chunk_timeout": 3000,   # 3s timeout for first chunk
    "auto_play_next_chapter": True,
}
```

### Data Storage Locations
- **Config**: `~/.config/novel-reader/config.json`
- **Database**: `~/.local/share/novel-reader/library.db`
- **Audio**: `~/.local/share/novel-reader/audio/`
- **Logs**: `~/.cache/novel-reader/logs/`

### TTS Voices (Edge TTS)
- **Chinese**: xiaoxiao, yunxi, yunjian, yunxia, xiaoyi, yunyang, hsiaochen, yunjia, hiuma, wanlung
- **English**: jenny, guy, aria, davis, jason, sonia, ryan, libby, natasha, william, neerja, prabhat

## Important Notes

### v1 vs v2 Architecture
- The codebase contains both v1 (legacy) and v2 (new) implementations
- New features should use v2 components (`models_v2.py`, `playback_controller_v2.py`, etc.)
- The GUI is being incrementally updated to use the new v2 controller
- When in doubt, prefer the v2 architecture

### No Formal Testing
- Tests directory exists but pytest is not yet configured
- Manual testing with debug prints is currently used

### Dependencies
- **PySide6** - GUI framework (includes QtMultimedia for audio playback)
- **edge-tts** - Microsoft Edge text-to-speech (online)
- **SQLite** - Local database (Python stdlib)

### Development Practices
- Use chunk-based navigation for granular seeking
- Always schedule TTS with appropriate priority
- Use audio cache to avoid redundant TTS conversions
- Thread safety: TTS and playback run in background threads
