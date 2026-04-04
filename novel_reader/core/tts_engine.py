"""
TTS Engine Interface

Provides text-to-speech conversion using Edge TTS (Microsoft neural voices).

Usage:
    from novel_reader.core.tts_engine import text_to_speech, convert_chunk, chunk_to_audio_path

    audio_path = text_to_speech("Hello world", "output.mp3")
    audio_path = convert_chunk("text", book_id=1, chunk_id=0)
"""
from pathlib import Path
from typing import Optional

from novel_reader.core import get_setting


AUDIO_DIR = Path("data/audio")


def chunk_to_audio_path(
        book_id: int,
        chunk_id: int,
        voice_id: Optional[str] = None,
) -> str:
    """
    Get audio file path for a chunk

    Args:
        book_id: Book ID
        chunk_id: Chunk ID
        voice_id: Voice ID (optional, uses setting)

    Returns:
        Audio file path (MP3 format)
    """
    voice_id = voice_id or get_setting("edge_chinese_voice_id", "xiaoxiao")
    return str(AUDIO_DIR / str(book_id) / f"chunk_edge_{voice_id}_{chunk_id:05d}.mp3")


def text_to_speech(
        text: str,
        output_path: str,
        **kwargs
) -> str:
    """
    Convert text to speech using Edge TTS

    Args:
        text: Input text
        output_path: Output audio file path
        **kwargs: Optional parameters:
            - chinese_voice_id, english_voice_id
            - rate, pitch, volume

    Returns:
        Path to generated audio file
    """
    from novel_reader.core.edge_tts import text_to_speech as edge_tts_func

    return edge_tts_func(text, output_path, **kwargs)


def convert_chunk(
        text: str,
        book_id: int,
        chunk_id: int,
        **kwargs
) -> str:
    """
    Convert a text chunk to audio

    Args:
        text: Chunk text
        book_id: Book ID
        chunk_id: Chunk ID

    Returns:
        Path to generated audio file
    """
    text = text.strip()
    if not text:
        raise ValueError(f"Chunk {chunk_id} text is empty")

    output_path = chunk_to_audio_path(book_id, chunk_id)
    result = text_to_speech(text, output_path, **kwargs)

    size = Path(result).stat().st_size
    if size == 0:
        raise RuntimeError("Audio file is empty")

    return result
