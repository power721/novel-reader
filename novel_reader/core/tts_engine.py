"""
Unified TTS Engine Interface

Provides a unified interface for both Piper and Edge TTS engines.
Routes TTS requests to the appropriate engine based on configuration.

Usage:
    from novel_reader.core.tts_engine import text_to_speech, get_tts_engine

    # Use default engine from settings
    audio_path = text_to_speech("Hello world", "output.wav")

    # Or specify engine explicitly
    audio_path = text_to_speech("Hello world", "output.wav", engine="edge")
"""
from pathlib import Path
from typing import Optional, List

from novel_reader.core import get_setting


class TTSEngine:
    """TTS Engine base class"""

    def __init__(self, engine_type: str):
        self.engine_type = engine_type

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Convert text to speech

        Args:
            text: Input text
            output_path: Output audio file path
            **kwargs: Additional engine-specific parameters

        Returns:
            Path to generated audio file

        Raises:
            NotImplementedError: Subclass must implement
        """
        raise NotImplementedError


class PiperTTSEngine(TTSEngine):
    """Piper TTS Engine implementation"""

    def __init__(self):
        super().__init__("piper")
        # Import Piper TTS functions
        from novel_reader.core.tts import (
            text_to_speech as piper_tts,
            check_models_available,
            warmup_piper,
        )
        self._text_to_speech = piper_tts
        self._check_models_available = check_models_available
        self._warmup = warmup_piper

    def is_available(self) -> bool:
        """Check if Piper TTS is available"""
        try:
            from novel_reader.core.tts import _check_piper_python
            return _check_piper_python()
        except ImportError:
            return False

    def warmup(self) -> bool:
        """Warmup Piper models"""
        try:
            return self._warmup()
        except Exception as e:
            print(f"⚠️ Piper warmup failed: {e}")
            return False

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        chinese_model_id: Optional[str] = None,
        english_model_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Convert text to speech using Piper TTS

        Args:
            text: Input text
            output_path: Output audio file path
            chinese_model_id: Chinese model ID (optional)
            english_model_id: English model ID (optional)
            **kwargs: Ignored for Piper

        Returns:
            Path to generated audio file
        """
        # Temporarily override settings if model IDs are provided
        if chinese_model_id or english_model_id:
            from novel_reader.core import settings

            old_zh = get_setting("chinese_model_id")
            old_en = get_setting("english_model_id")

            if chinese_model_id:
                settings.set_setting("chinese_model_id", chinese_model_id)
            if english_model_id:
                settings.set_setting("english_model_id", english_model_id)

            try:
                result = self._text_to_speech(text, output_path)
            finally:
                # Restore original settings
                if chinese_model_id:
                    settings.set_setting("chinese_model_id", old_zh)
                if english_model_id:
                    settings.set_setting("english_model_id", old_en)

            return result

        return self._text_to_speech(text, output_path)


class EdgeTTSEngine(TTSEngine):
    """Edge TTS Engine implementation"""

    def __init__(self):
        super().__init__("edge")
        # Import Edge TTS functions
        from novel_reader.core.edge_tts import (
            text_to_speech as edge_tts,
            check_edge_tts_available,
        )
        self._text_to_speech = edge_tts
        self._check_available = check_edge_tts_available

    def is_available(self) -> bool:
        """Check if Edge TTS is available"""
        return self._check_available()

    def warmup(self) -> bool:
        """Warmup Edge TTS (no-op, no models to load)"""
        return True

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        chinese_voice_id: Optional[str] = None,
        english_voice_id: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Convert text to speech using Edge TTS

        Args:
            text: Input text
            output_path: Output audio file path
            chinese_voice_id: Chinese voice ID (optional)
            english_voice_id: English voice ID (optional)
            rate: Speaking rate (e.g., "+0%", "+10%")
            pitch: Pitch adjustment (e.g., "+0Hz", "+10Hz")
            volume: Volume adjustment (e.g., "+0%", "+10%")
            **kwargs: Ignored for Edge TTS

        Returns:
            Path to generated audio file
        """
        # Get parameters from settings if not provided
        if not rate:
            rate = get_setting("edge_rate", "+0%")
        if not pitch:
            pitch = get_setting("edge_pitch", "+0Hz")
        if not volume:
            volume = get_setting("edge_volume", "+0%")

        return self._text_to_speech(
            text,
            output_path,
            chinese_voice_id=chinese_voice_id,
            english_voice_id=english_voice_id,
            rate=rate,
            pitch=pitch,
            volume=volume,
            convert_to_wav=True
        )


# ==================== Engine Factory ====================

_engines: dict = {
    "piper": None,
    "edge": None,
}


def get_engine(engine_type: str) -> TTSEngine:
    """
    Get TTS engine instance (singleton)

    Args:
        engine_type: Engine type ("piper" or "edge")

    Returns:
        TTSEngine instance

    Raises:
        ValueError: If engine type is unknown
    """
    global _engines

    if engine_type not in _engines:
        raise ValueError(f"Unknown TTS engine: {engine_type}. Available: {list(_engines.keys())}")

    if _engines[engine_type] is None:
        if engine_type == "piper":
            _engines[engine_type] = PiperTTSEngine()
        elif engine_type == "edge":
            _engines[engine_type] = EdgeTTSEngine()

    return _engines[engine_type]


def get_current_engine() -> TTSEngine:
    """
    Get current TTS engine based on settings

    Returns:
        TTSEngine instance

    Raises:
        ValueError: If configured engine is not available
    """
    engine_type = get_setting("tts_engine", "piper")
    engine = get_engine(engine_type)

    if not engine.is_available():
        # Try fallback
        available = get_available_engines()
        if available:
            print(f"⚠️ TTS engine '{engine_type}' not available, falling back to '{available[0]}'")
            engine = get_engine(available[0])
        else:
            raise RuntimeError(f"No TTS engine available. Please install piper-tts or edge-tts")

    return engine


def get_available_engines() -> List[str]:
    """
    Get list of available TTS engines

    Returns:
        List of available engine types
    """
    available = []
    for engine_type in ["piper", "edge"]:
        try:
            engine = get_engine(engine_type)
            if engine.is_available():
                available.append(engine_type)
        except Exception:
            pass
    return available


def warmup_current_engine() -> bool:
    """
    Warmup current TTS engine

    Returns:
        True if successful, False otherwise
    """
    try:
        engine = get_current_engine()
        return engine.warmup()
    except Exception as e:
        print(f"⚠️ TTS engine warmup failed: {e}")
        return False


def text_to_speech(
    text: str,
    output_path: str,
    engine: Optional[str] = None,
    **kwargs
) -> str:
    """
    Unified text-to-speech interface

    Automatically routes to the appropriate TTS engine based on configuration.

    Args:
        text: Input text
        output_path: Output audio file path
        engine: Engine type ("piper" or "edge"). If None, uses setting
        **kwargs: Engine-specific parameters:
            - For Piper: chinese_model_id, english_model_id
            - For Edge: chinese_voice_id, english_voice_id, rate, pitch, volume

    Returns:
        Path to generated audio file

    Raises:
        RuntimeError: If no TTS engine is available
    """
    if engine:
        tts_engine = get_engine(engine)
        if not tts_engine.is_available():
            available = get_available_engines()
            raise RuntimeError(
                f"TTS engine '{engine}' not available. "
                f"Available engines: {available}"
            )
    else:
        tts_engine = get_current_engine()

    return tts_engine.text_to_speech(text, output_path, **kwargs)


def chunk_to_audio_path(
    book_id: int,
    chunk_id: int,
    voice_id: Optional[str] = None,
    engine: Optional[str] = None
) -> str:
    """
    Get audio file path for a chunk

    Args:
        book_id: Book ID
        chunk_id: Chunk ID
        voice_id: Voice/model ID (optional)
        engine: Engine type (optional)

    Returns:
        Audio file path
    """
    from novel_reader.core.tts import AUDIO_DIR

    if engine == "edge" or (not engine and get_setting("tts_engine", "piper") == "edge"):
        voice_id = voice_id or get_setting("edge_chinese_voice_id", "xiaoxiao")
        return str(AUDIO_DIR / str(book_id) / f"chunk_edge_{voice_id}_{chunk_id:05d}.wav")
    else:
        voice_id = voice_id or get_setting("chinese_model_id", "xiao_ya")
        return str(AUDIO_DIR / str(book_id) / f"chunk_{voice_id}_{chunk_id:05d}.wav")


def convert_chunk(
    text: str,
    book_id: int,
    chunk_id: int,
    engine: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convert a text chunk to audio

    Args:
        text: Chunk text
        book_id: Book ID
        chunk_id: Chunk ID
        engine: Engine type (optional)
        **kwargs: Engine-specific parameters

    Returns:
        Path to generated audio file
    """
    text = text.strip()
    if not text:
        raise ValueError(f"Chunk {chunk_id} text is empty")

    output_path = chunk_to_audio_path(book_id, chunk_id, engine=engine)

    result = text_to_speech(text, output_path, engine=engine, **kwargs)

    size = Path(result).stat().st_size
    if size == 0:
        raise RuntimeError("Audio file is empty")

    # engine_name = engine or get_setting("tts_engine", "piper")
    # print(f"✓ Chunk {chunk_id} OK ({size / 1024:.1f} KB) [{engine_name.upper()}]")

    return result


# ==================== Test Code ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Unified TTS Engine Test")
    print("=" * 60)

    # Test available engines
    print("\n[1] Available TTS Engines:")
    available = get_available_engines()
    print(f"  Available: {available}")
    print(f"  Current engine: {get_setting('tts_engine', 'piper')}")

    # Test getting engines
    print("\n[2] Getting Engine Instances:")
    try:
        piper = get_engine("piper")
        print(f"  Piper: {'available' if piper.is_available() else 'not available'}")
    except Exception as e:
        print(f"  Piper: {e}")

    try:
        edge = get_engine("edge")
        print(f"  Edge: {'available' if edge.is_available() else 'not available'}")
    except Exception as e:
        print(f"  Edge: {e}")

    # Test text to speech
    print("\n[3] Testing Text-to-Speech:")
    test_text = "你好，世界。Hello, world."

    try:
        output_file = "test_unified_tts_output.wav"
        print(f"  Converting: '{test_text}'")

        result = text_to_speech(test_text, output_file)
        print(f"  ✓ Output: {result}")
        print(f"  File size: {Path(result).stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
