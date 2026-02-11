"""
Edge TTS Voice Configuration Module

Manages all available Edge TTS voices (Microsoft Azure Cognitive Services)

Edge TTS uses Microsoft's online neural TTS voices.
Documentation: https://github.com/rany2/edge-tts
Voice list: https://speech.platform.bing.com/consumer/cogne/online/v1/api
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EdgeTTSVoice:
    """
    Edge TTS Voice Definition

    Attributes:
        id: Voice unique identifier (short name for settings)
        name: Full Edge TTS voice name (e.g., "zh-CN-XiaoxiaoNeural")
        title: Display name (friendly name for UI)
        language: Language code ("zh", "en")
        locale: Full locale code (e.g., "zh-CN", "en-US")
        gender: Voice gender ("Male", "Female")
        description: Voice description
        recommended: Whether this voice is recommended
    """
    id: str
    name: str
    title: str
    language: str
    locale: str
    gender: str
    description: str
    recommended: bool = False

    def __repr__(self) -> str:
        return f"EdgeTTSVoice(id={self.id}, name={self.name}, title={self.title})"


# ==================== Voice Registry ====================

# Chinese voices (zh-CN)
ZH_VOICES: List[EdgeTTSVoice] = [
    EdgeTTSVoice(
        id="xiaoxiao",
        name="zh-CN-XiaoxiaoNeural",
        title="晓潇 (Xiaoxiao)",
        language="zh",
        locale="zh-CN",
        gender="Female",
        description="女声，温柔自然",
        recommended=True
    ),
    EdgeTTSVoice(
        id="yunxi",
        name="zh-CN-YunxiNeural",
        title="云希 (Yunxi)",
        language="zh",
        locale="zh-CN",
        gender="Male",
        description="男声，温暖亲切",
        recommended=True
    ),
    EdgeTTSVoice(
        id="yunjian",
        name="zh-CN-YunjianNeural",
        title="云健 (Yunjian)",
        language="zh",
        locale="zh-CN",
        gender="Male",
        description="男声，成熟稳重"
    ),
    EdgeTTSVoice(
        id="yunxia",
        name="zh-CN-YunxiaNeural",
        title="云霞 (Yunxia)",
        language="zh",
        locale="zh-CN",
        gender="Female",
        description="女声，成熟温和"
    ),
    EdgeTTSVoice(
        id="xiaoyi",
        name="zh-CN-XiaoyiNeural",
        title="晓伊 (Xiaoyi)",
        language="zh",
        locale="zh-CN",
        gender="Female",
        description="女声，年轻活泼"
    ),
    EdgeTTSVoice(
        id="yunyang",
        name="zh-CN-YunyangNeural",
        title="云扬 (Yunyang)",
        language="zh",
        locale="zh-CN",
        gender="Male",
        description="男声，年轻热情"
    ),
    # Taiwan voices
    EdgeTTSVoice(
        id="hsiaochen",
        name="zh-TW-HsiaoChenNeural",
        title="曉臻 (HsiaoChen)",
        language="zh",
        locale="zh-TW",
        gender="Female",
        description="台灣女聲，溫柔自然"
    ),
    EdgeTTSVoice(
        id="yunjia",
        name="zh-TW-YunJiaNeural",
        title="雲嘉 (YunJia)",
        language="zh",
        locale="zh-TW",
        gender="Male",
        description="台灣男聲，溫暖親切"
    ),
    # Hong Kong voices
    EdgeTTSVoice(
        id="hiuma",
        name="zh-HK-HiuMaanNeural",
        title="曉文 (HiuMaan)",
        language="zh",
        locale="zh-HK",
        gender="Female",
        description="香港女聲，溫柔自然"
    ),
    EdgeTTSVoice(
        id="wanlung",
        name="zh-HK-WanLungNeural",
        title="文龍 (WanLung)",
        language="zh",
        locale="zh-HK",
        gender="Male",
        description="香港男聲，成熟穩重"
    ),
]

# English voices
EN_VOICES: List[EdgeTTSVoice] = [
    EdgeTTSVoice(
        id="jenny",
        name="en-US-JennyNeural",
        title="Jenny",
        language="en",
        locale="en-US",
        gender="Female",
        description="American female, friendly and natural",
        recommended=True
    ),
    EdgeTTSVoice(
        id="guy",
        name="en-US-GuyNeural",
        title="Guy",
        language="en",
        locale="en-US",
        gender="Male",
        description="American male, warm and confident",
        recommended=True
    ),
    EdgeTTSVoice(
        id="aria",
        name="en-US-AriaNeural",
        title="Aria",
        language="en",
        locale="en-US",
        gender="Female",
        description="American female, expressive and engaging"
    ),
    EdgeTTSVoice(
        id="davis",
        name="en-US-DavisNeural",
        title="Davis",
        language="en",
        locale="en-US",
        gender="Male",
        description="American male, clear and professional"
    ),
    EdgeTTSVoice(
        id="jason",
        name="en-US-JasonNeural",
        title="Jason",
        language="en",
        locale="en-US",
        gender="Male",
        description="American male, youthful and energetic"
    ),
    # UK English
    EdgeTTSVoice(
        id="sonia",
        name="en-GB-SoniaNeural",
        title="Sonia",
        language="en",
        locale="en-GB",
        gender="Female",
        description="British female, natural and calm"
    ),
    EdgeTTSVoice(
        id="ryan",
        name="en-GB-RyanNeural",
        title="Ryan",
        language="en",
        locale="en-GB",
        gender="Male",
        description="British male, warm and friendly"
    ),
    EdgeTTSVoice(
        id="libby",
        name="en-GB-LibbyNeural",
        title="Libby",
        language="en",
        locale="en-GB",
        gender="Female",
        description="British female, youthful and cheerful"
    ),
    # Australian English
    EdgeTTSVoice(
        id="natasha",
        name="en-AU-NatashaNeural",
        title="Natasha",
        language="en",
        locale="en-AU",
        gender="Female",
        description="Australian female, friendly and natural"
    ),
    EdgeTTSVoice(
        id="william",
        name="en-AU-WilliamNeural",
        title="William",
        language="en",
        locale="en-AU",
        gender="Male",
        description="Australian male, warm and confident"
    ),
    # Indian English
    EdgeTTSVoice(
        id="neerja",
        name="en-IN-NeerjaNeural",
        title="Neerja",
        language="en",
        locale="en-IN",
        gender="Female",
        description="Indian female, calm and professional"
    ),
    EdgeTTSVoice(
        id="prabhat",
        name="en-IN-PrabhatNeural",
        title="Prabhat",
        language="en",
        locale="en-IN",
        gender="Male",
        description="Indian male, deep and measured"
    ),
]

# All voices
ALL_VOICES = ZH_VOICES + EN_VOICES

# Default voices
DEFAULT_CHINESE_VOICE = "xiaoxiao"
DEFAULT_ENGLISH_VOICE = "jenny"


# ==================== Query Functions ====================

def get_voice(voice_id: str) -> Optional[EdgeTTSVoice]:
    """
    Get voice by ID

    Args:
        voice_id: Voice ID

    Returns:
        EdgeTTSVoice object or None if not found
    """
    for voice in ALL_VOICES:
        if voice.id == voice_id:
            return voice
    return None


def get_voices_by_language(language: str) -> List[EdgeTTSVoice]:
    """
    Get voices by language

    Args:
        language: Language code ("zh" or "en")

    Returns:
        List of voices
    """
    if language == "zh":
        return ZH_VOICES.copy()
    elif language == "en":
        return EN_VOICES.copy()
    return []


def get_default_voice(language: str) -> Optional[EdgeTTSVoice]:
    """
    Get default voice for language

    Args:
        language: Language code ("zh" or "en")

    Returns:
        Default voice or None if not found
    """
    if language == "zh":
        return get_voice(DEFAULT_CHINESE_VOICE)
    elif language == "en":
        return get_voice(DEFAULT_ENGLISH_VOICE)
    return None


def list_voice_ids(language: str = None) -> List[str]:
    """
    List all voice IDs

    Args:
        language: Optional, filter by language

    Returns:
        List of voice IDs
    """
    if language:
        voices = get_voices_by_language(language)
    else:
        voices = ALL_VOICES
    return [v.id for v in voices]


def get_voice_title(voice_id: str) -> str:
    """
    Get voice display title

    Args:
        voice_id: Voice ID

    Returns:
        Display title, or voice_id if not found
    """
    voice = get_voice(voice_id)
    if voice:
        return voice.title
    return voice_id


def get_recommended_voices(language: str) -> List[EdgeTTSVoice]:
    """
    Get recommended voices for language

    Args:
        language: Language code ("zh" or "en")

    Returns:
        List of recommended voices
    """
    voices = get_voices_by_language(language)
    return [v for v in voices if v.recommended]


# ==================== Test Code ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Edge TTS Voice Configuration Test")
    print("=" * 60)

    # Test Chinese voices
    print("\n[1] Chinese Voices:")
    for voice in ZH_VOICES:
        rec = " (推荐)" if voice.recommended else ""
        print(f"  - {voice.id}: {voice.title} ({voice.gender}){rec}")

    # Test English voices
    print("\n[2] English Voices:")
    for voice in EN_VOICES:
        rec = " (推荐)" if voice.recommended else ""
        print(f"  - {voice.id}: {voice.title} ({voice.gender}){rec}")

    # Test query functions
    print("\n[3] Query Test:")
    xiaoxiao = get_voice("xiaoxiao")
    print(f"  xiaoxiao: {xiaoxiao}")

    jenny = get_voice("jenny")
    print(f"  jenny: {jenny}")

    not_found = get_voice("not_exist")
    print(f"  not_exist: {not_found}")

    # Test default voices
    print("\n[4] Default Voices:")
    print(f"  Chinese default: {get_default_voice('zh')}")
    print(f"  English default: {get_default_voice('en')}")

    # Test recommended voices
    print("\n[5] Recommended Voices:")
    zh_rec = get_recommended_voices("zh")
    print(f"  Chinese recommended: {[v.id for v in zh_rec]}")
    en_rec = get_recommended_voices("en")
    print(f"  English recommended: {[v.id for v in en_rec]}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
