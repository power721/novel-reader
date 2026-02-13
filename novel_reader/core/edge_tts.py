"""
Edge TTS Module - Microsoft Edge Text-to-Speech

Uses edge-tts library to generate speech from text using Microsoft's
online neural TTS voices.

Installation:
    pip install edge-tts

Documentation:
    https://github.com/rany2/edge-tts

This module provides:
1. Text-to-speech conversion with mixed Chinese/English support
2. Voice management with Chinese and English voices
3. MP3 audio output (Edge TTS only supports MP3)
4. Async and sync conversion methods
"""
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# Import voice configuration
from novel_reader.core.edge_tts_config import (
    get_voice,
    get_voices_by_language,
    DEFAULT_CHINESE_VOICE,
    DEFAULT_ENGLISH_VOICE,
)

# Import text processing from Piper TTS
from novel_reader.core.tts import (
    normalize_for_novel_tts,
)


# ==================== Audio Conversion ====================

def mp3_to_wav(mp3_path: str, wav_path: str) -> bool:
    """
    Convert MP3 to WAV using ffmpeg

    Args:
        mp3_path: Input MP3 file path
        wav_path: Output WAV file path

    Returns:
        True if successful, False otherwise
    """
    try:
        import subprocess

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-i", mp3_path,
            "-ar", "22050",  # Sample rate to match Piper
            "-ac", "1",  # Mono
            wav_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if result.returncode == 0:
            return True
        else:
            print(f"⚠️ ffmpeg conversion failed: {result.stderr.decode()}")
            return False
    except FileNotFoundError:
        print("⚠️ ffmpeg not found, MP3 will not be converted to WAV")
        return False
    except Exception as e:
        print(f"⚠️ ffmpeg conversion error: {e}")
        return False


def convert_audio_to_wav(input_path: str, output_path: str) -> str:
    """
    Convert audio file to WAV format

    Edge TTS outputs MP3, so we need to convert to WAV for compatibility.

    Args:
        input_path: Input audio file path
        output_path: Output WAV file path

    Returns:
        Path to WAV file (either converted or original)
    """
    input_file = Path(input_path)

    # If already WAV, return as-is
    if input_file.suffix.lower() == '.wav':
        return input_path

    # Try to convert to WAV
    if mp3_to_wav(input_path, output_path):
        return output_path

    # Fallback: return original MP3
    print(f"⚠️ Using original MP3 file (not converted)")
    return input_path


# ==================== Edge TTS Core Functions ====================

def check_edge_tts_available() -> bool:
    """Check if edge-tts is available"""
    return EDGE_TTS_AVAILABLE


async def _text_to_speech_async(
        text: str,
        voice_name: str,
        output_path: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
) -> str:
    """
    Async text-to-speech using Edge TTS

    Args:
        text: Input text
        voice_name: Edge TTS voice name (e.g., "zh-CN-XiaoxiaoNeural")
        output_path: Output file path (will be MP3)
        rate: Speaking rate (e.g., "+0%", "+10%", "-10%")
        pitch: Pitch adjustment (e.g., "+0Hz", "+10Hz")
        volume: Volume adjustment (e.g., "+0%", "+10%")

    Returns:
        Path to generated audio file
    """
    print(f"[edge_tts._text_to_speech_async] DEBUG: voice={voice_name} rate={rate}, pitch={pitch}, volume={volume}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create communicate object
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_name,
        rate=rate,
        pitch=pitch,
        volume=volume
    )

    # Save to file
    await communicate.save(str(output_file))

    return str(output_file)


def _text_to_speech_sync(
        text: str,
        voice_name: str,
        output_path: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
) -> str:
    """
    Synchronous wrapper for Edge TTS

    Args:
        text: Input text
        voice_name: Edge TTS voice name
        output_path: Output file path
        rate: Speaking rate
        pitch: Pitch adjustment
        volume: Volume adjustment

    Returns:
        Path to generated audio file
    """
    return asyncio.run(_text_to_speech_async(
        text, voice_name, output_path, rate, pitch, volume
    ))


def text_to_speech(
        text: str,
        output_path: str,
        chinese_voice_id: Optional[str] = None,
        english_voice_id: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
        convert_to_wav: bool = True
) -> str:
    """
    Mixed Chinese/English text-to-speech using Edge TTS

    Automatically detects Chinese and English text segments and uses
    appropriate voices for each.

    Args:
        text: Input text (can contain mixed Chinese/English)
        output_path: Output audio file path
        chinese_voice_id: Chinese voice ID (default: xiaoxiao)
        english_voice_id: English voice ID (default: jenny)
        rate: Speaking rate adjustment (e.g., "+0%", "+10%")
        pitch: Pitch adjustment (e.g., "+0Hz", "+10Hz")
        volume: Volume adjustment (e.g., "+0%", "+10%")
        convert_to_wav: Convert MP3 to WAV for compatibility

    Returns:
        Path to generated audio file

    Raises:
        ImportError: If edge-tts is not installed
        ValueError: If text is empty
        RuntimeError: If TTS conversion fails
    """
    if not EDGE_TTS_AVAILABLE:
        raise ImportError(
            "edge-tts is not installed. Install it with:\n"
            "    pip install edge-tts"
        )

    text = text.strip()
    if not text:
        raise ValueError("文本为空")

    # Apply full novel normalization for Chinese
    text = normalize_for_novel_tts(text)

    # Get voice IDs from settings if not provided
    from novel_reader.core import get_setting
    if not chinese_voice_id:
        chinese_voice_id = get_setting("edge_chinese_voice_id", DEFAULT_CHINESE_VOICE)

    if not english_voice_id:
        english_voice_id = get_setting("edge_english_voice_id", DEFAULT_ENGLISH_VOICE)

    zh_voice_id = chinese_voice_id
    en_voice_id = english_voice_id

    zh_voice = get_voice(zh_voice_id)
    en_voice = get_voice(en_voice_id)

    if not zh_voice:
        raise ValueError(f"Chinese voice not found: {zh_voice_id}")
    if not en_voice:
        raise ValueError(f"English voice not found: {en_voice_id}")

    # Split text by language first (before normalization)
    # We use a simple split without normalization to determine language segments
    # sentences = split_text_for_tts(text)
    sentences = [(text, "zh")] # TODO: detect language

    # Filter out empty or punctuation-only segments
    filtered_sentences = []
    for sent_text, sent_lang in sentences:
        # Check if segment contains actual alphanumeric characters
        import re
        if re.search(r'[a-zA-Z0-9\u4e00-\u9fff]', sent_text):
            filtered_sentences.append((sent_text, sent_lang))
        else:
            # Merge punctuation with previous segment or skip
            if filtered_sentences:
                # Append to previous segment
                prev_text, prev_lang = filtered_sentences[-1]
                filtered_sentences[-1] = (prev_text + sent_text, prev_lang)

    sentences = filtered_sentences

    if not sentences:
        # If no split needed, use Chinese voice for all
        sentences = [(text, "zh")]

    # Normalize each segment based on its language
    normalized_sentences = []
    for sent_text, sent_lang in sentences:
        if sent_lang == "zh":
            normalized_sentences.append((sent_text, "zh"))
        else:
            normalized_sentences.append((sent_text, "en"))

    sentences = normalized_sentences

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Single sentence - direct output
    if len(sentences) == 1:
        sent_text, sent_lang = sentences[0]
        voice = en_voice if sent_lang == 'en' else zh_voice

        # Edge TTS outputs MP3
        mp3_path = str(output_file).replace('.wav', '.mp3') if output_file.suffix == '.wav' else str(output_file)
        if not mp3_path.endswith('.mp3'):
            mp3_path = mp3_path + '.mp3'

        _text_to_speech_sync(sent_text, voice.name, mp3_path, rate, pitch, volume)

        # Convert to WAV if requested
        if convert_to_wav:
            return convert_audio_to_wav(mp3_path, str(output_file))
        return mp3_path

    # Multiple sentences - need to merge
    # For mixed text, we need to concatenate multiple audio files
    # Create a temp directory for intermediate files
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        temp_files = []
        fallback_file = None  # Store first segment as fallback

        # Use a single async loop for all segments to avoid event loop issues
        async def convert_all_segments():
            results = []
            for idx, sent in enumerate(sentences):
                voice = en_voice if sent[1] == 'en' else zh_voice
                temp_mp3 = Path(tmp) / f"{idx:04d}.mp3"

                print(
                    f"[edge_tts] Converting segment {idx}/{len(sentences)}: voice={voice.id}, text=\"{sent[0][:30]}...\"")

                # Create communicate object
                communicate = edge_tts.Communicate(
                    text=sent[0],
                    voice=voice.name,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )

                # Save to file
                await communicate.save(str(temp_mp3))

                # Verify the MP3 was created
                if not temp_mp3.exists():
                    raise RuntimeError(f"Failed to generate audio for segment {idx}")

                print(f"[edge_tts] Segment {idx} completed: {temp_mp3.stat().st_size} bytes")
                results.append(str(temp_mp3))

                # Small delay between segments
                if idx < len(sentences) - 1:
                    await asyncio.sleep(0.1)

            return results

        # Run all conversions in a single event loop
        try:
            temp_files = asyncio.run(convert_all_segments())
        except Exception as e:
            raise RuntimeError(f"Failed to convert segments: {e}")

        # Store first segment as fallback (copy it outside temp dir before it's deleted)
        if temp_files:
            import shutil
            fallback_mp3 = Path(output_file.parent) / f"temp_fallback_{output_file.stem}.mp3"
            shutil.copy2(temp_files[0], str(fallback_mp3))
            fallback_file = str(fallback_mp3)
            print(f"[edge_tts] Created fallback file: {fallback_mp3.name}")
        else:
            raise RuntimeError("No segments were successfully converted")

            # Verify the MP3 was created
            if not temp_mp3.exists():
                raise RuntimeError(f"Failed to generate audio for segment {idx}")

            # Store first segment as fallback
            if idx == 0:
                # Copy first segment to a permanent location for fallback
                fallback_mp3 = Path(output_file.parent) / f"temp_fallback_{output_file.stem}.mp3"
                import shutil
                shutil.copy2(temp_mp3, fallback_mp3)
                fallback_file = str(fallback_mp3)

            temp_files.append(str(temp_mp3))

        # Determine output MP3 path
        output_mp3 = str(output_file).replace('.wav', '.mp3') if output_file.suffix == '.wav' else str(output_file)
        if not output_mp3.endswith('.mp3'):
            output_mp3 = output_mp3 + '.mp3'

        # Try to concatenate
        try:
            result = concat_mp3s(temp_files, output_mp3)

            # Check if result is a temp file (indicates concat failed)
            if result and result in temp_files:
                print(f"⚠️ Concatenation failed, using first segment only")
                if fallback_file:
                    if convert_to_wav:
                        return convert_audio_to_wav(fallback_file, str(output_file))
                    return fallback_file
                else:
                    raise RuntimeError("Concatenation failed and no fallback available")

            # Verify concatenation worked
            if result and Path(result).exists() and Path(result).stat().st_size > 0:
                # Clean up fallback file
                if fallback_file and Path(fallback_file).exists():
                    Path(fallback_file).unlink(missing_ok=True)
                # Convert to WAV if requested
                if convert_to_wav:
                    return convert_audio_to_wav(result, str(output_file))
                return result
            else:
                # Fallback: use first segment
                print(f"⚠️ Concatenation produced invalid output, using first segment only")
                if fallback_file:
                    if convert_to_wav:
                        return convert_audio_to_wav(fallback_file, str(output_file))
                    return fallback_file
                else:
                    raise RuntimeError("Concatenation failed and no fallback available")

        except Exception as e:
            print(f"⚠️ Audio concatenation error: {e}")
            # Fallback: use first segment
            print(f"⚠️ Using first segment only")
            if fallback_file:
                if convert_to_wav:
                    return convert_audio_to_wav(fallback_file, str(output_file))
                return fallback_file
            else:
                raise

    return str(output_file)


def concat_mp3s(mp3_files: List[str], output_path: str) -> str:
    """
    Concatenate MP3 files using ffmpeg

    Args:
        mp3_files: List of MP3 file paths
        output_path: Output file path

    Returns:
        Output file path
    """
    try:
        import subprocess

        # Create temporary file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for mp3 in mp3_files:
                f.write(f"file '{Path(mp3).absolute()}'\n")
            list_file = f.name

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        Path(list_file).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"⚠️ ffmpeg concat failed: {result.stderr.decode()}")
            # Fallback: return first file
            return mp3_files[0] if mp3_files else output_path

        return output_path

    except Exception as e:
        print(f"⚠️ MP3 concatenation error: {e}")
        return mp3_files[0] if mp3_files else output_path


# ==================== Voice Management ====================

def list_available_voices(language: str = None) -> List[str]:
    """
    List available Edge TTS voices

    Args:
        language: Optional language filter ("zh" or "en")

    Returns:
        List of voice IDs
    """
    if language:
        voices = get_voices_by_language(language)
    else:
        voices = get_voices_by_language("zh") + get_voices_by_language("en")
    return [v.id for v in voices]


def get_recommended_voices(language: str) -> List[str]:
    """
    Get recommended voices for language

    Args:
        language: Language code ("zh" or "en")

    Returns:
        List of recommended voice IDs
    """
    voices = get_voices_by_language(language)
    return [v.id for v in voices if v.recommended]


# ==================== Chunk Interface (compatible with Piper) ====================

def chunk_to_audio_path(book_id: int, chunk_id: int, voice_id: str = "xiaoxiao") -> str:
    """
    Get audio file path for a chunk

    Args:
        book_id: Book ID
        chunk_id: Chunk ID
        voice_id: Voice ID

    Returns:
        Audio file path
    """
    from novel_reader.core.tts import AUDIO_DIR
    return str(AUDIO_DIR / str(book_id) / f"chunk_edge_{voice_id}_{chunk_id:05d}.wav")


def convert_chunk(
        text: str,
        book_id: int,
        chunk_id: int,
        chinese_voice_id: Optional[str] = None,
        english_voice_id: Optional[str] = None
) -> str:
    """
    Convert a text chunk to audio using Edge TTS

    Args:
        text: Chunk text
        book_id: Book ID
        chunk_id: Chunk ID
        chinese_voice_id: Chinese voice ID (optional)
        english_voice_id: English voice ID (optional)

    Returns:
        Path to generated audio file

    Raises:
        ValueError: If text is empty
        RuntimeError: If conversion fails
    """
    text = text.strip()
    if not text:
        raise ValueError(f"Chunk {chunk_id} text is empty")

    # Get voice IDs from settings if not provided
    from novel_reader.core import get_setting
    if not chinese_voice_id:
        chinese_voice_id = get_setting("edge_chinese_voice_id", DEFAULT_CHINESE_VOICE)

    if not english_voice_id:
        english_voice_id = get_setting("edge_english_voice_id", DEFAULT_ENGLISH_VOICE)

    output = chunk_to_audio_path(book_id, chunk_id, chinese_voice_id)

    try:
        path = text_to_speech(
            text,
            output,
            chinese_voice_id=chinese_voice_id,
            english_voice_id=english_voice_id,
            convert_to_wav=True
        )

        size = Path(path).stat().st_size
        if size == 0:
            raise RuntimeError("Audio file is empty")

        print(f"✓ Chunk {chunk_id} OK ({size / 1024:.1f} KB) [Edge TTS]")
        return path

    except Exception as e:
        print(f"✗ Chunk {chunk_id} failed: {e} [Edge TTS]")
        if Path(output).exists():
            Path(output).unlink(missing_ok=True)
        raise


# ==================== Test Code ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Edge TTS Module Test")
    print("=" * 60)

    # Check availability
    print("\n[1] Checking Edge TTS availability...")
    if check_edge_tts_available():
        print("✓ edge-tts is available")
    else:
        print("✗ edge-tts is not installed")
        print("  Install with: pip install edge-tts")
        exit(1)

    # Test voice listing
    print("\n[2] Available voices:")
    zh_voices = list_available_voices("zh")
    print(f"  Chinese voices: {len(zh_voices)}")
    print(f"  Recommended: {get_recommended_voices('zh')}")

    en_voices = list_available_voices("en")
    print(f"  English voices: {len(en_voices)}")
    print(f"  Recommended: {get_recommended_voices('en')}")

    # Test TTS
    print("\n[3] Testing text-to-speech...")
    test_text = "你好，我是晓潇。Hello, I am Xiaoxiao."

    try:
        output_file = "test_edge_tts_output.wav"
        print(f"  Converting: '{test_text}'")

        result = text_to_speech(
            test_text,
            output_file,
            chinese_voice_id="xiaoxiao",
            english_voice_id="jenny"
        )

        print(f"  ✓ Output: {result}")
        print(f"  File size: {Path(result).stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
