# Changelog

All notable changes to Novel Reader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release

### Changed
- Migrated to QMediaPlayer from mpv-based playback
- Refactored to v2 architecture with modular components

### Fixed
- Various bug fixes and improvements

## [1.0.0] - 2024-XX-XX

### Added
- Edge TTS integration for text-to-speech
- Chunk-based architecture for seamless playback
- Priority-based TTS scheduling
- Audio caching with LRU eviction
- PySide6 GUI with chapter navigation
- Bookmark and progress persistence
- Ebook import (EPUB, MOBI)
- Reading mode with auto-scroll and auto-play
- Theme support (dark mode, eye protection mode)
- Audio compact mode for focused reading

### Changed
- Complete rewrite of playback engine
- Improved performance with intelligent caching

### Fixed
- Chapter navigation issues
- TTS timeout handling
- Input method support on Linux

[Unreleased]: https://github.com/yourusername/novel-reader/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/novel-reader/releases/tag/v1.0.0
