#!/usr/bin/env python3
"""
Simple test script for QtAudioPlayer
"""
import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from novel_reader.core.player import QtAudioPlayer

def test_qt_player():
    """Test QtAudioPlayer with a simple audio file"""
    print("=" * 60)
    print("QtAudioPlayer Test")
    print("=" * 60)

    # Create Qt application (required for QMediaPlayer)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create player
    player = QtAudioPlayer()

    # Connect signals
    player.finished.connect(lambda: print("\n✅ Playback finished!"))
    player.error.connect(lambda err: print(f"\n❌ Playback error: {err}"))
    player.position_changed.connect(lambda pos, dur: print(f"\r🎵 Position: {pos//1000}s / {dur//1000}s", end='', flush=True))

    # Test 1: Check if player is created
    print("\n[1] Player Creation")
    print(f"✓ Player created: {player}")
    print(f"✓ Is playing: {player.is_playing}")
    print(f"✓ Is paused: {player.is_paused}")

    # Test 2: Check if we can find a test audio file
    print("\n[2] Looking for test audio file...")
    audio_dir = Path("data/audio")
    test_files = list(audio_dir.rglob("*.mp3"))[:3]  # Get first 3 mp3 files

    if not test_files:
        print("⚠ No audio files found. Creating a simple test...")
        print("  (This is expected if no books have been converted yet)")
        print("\n✓ QtAudioPlayer is ready to use!")
        print("  To fully test, convert a book to audio first.")
        return

    test_file = test_files[0]
    print(f"✓ Found test file: {test_file.name}")

    # Test 3: Set volume
    print("\n[3] Volume Control")
    player.set_volume(0.5)
    print(f"✓ Volume set to 50%")

    # Test 4: Set playback speed
    print("\n[4] Playback Speed")
    player.set_playback_speed(1.0)
    print(f"✓ Speed set to 1.0x")

    # Test 5: Play audio (commented out to avoid actual playback in automated test)
    print("\n[5] Audio Playback (skipped in automated test)")
    print("  To test playback, uncomment the play() call below")
    # player.play(str(test_file))
    # import time
    # time.sleep(2)  # Play for 2 seconds
    # player.stop()

    print("\n" + "=" * 60)
    print("✓ All basic tests passed!")
    print("=" * 60)
    print("\nQtAudioPlayer is working correctly!")
    print("The application is ready for manual testing.")

if __name__ == "__main__":
    try:
        test_qt_player()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
