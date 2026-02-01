"""
TTS 模块 - 使用 Piper 将文本转换为语音

支持两种方式：
1. Python API (pip install piper-tts) - 优先使用
2. subprocess 调用 piper 命令行工具

模型下载：
https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0

推荐模型：
- 英文：en_US-lessac-medium.onnx
- 中文：zh_CN-xiao_ya-medium.onnx
"""
import os
import re
import subprocess
import tempfile
import threading
import wave
from pathlib import Path
from typing import Optional, List, Tuple

# ==================== 环境配置 ====================

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
CACHE_DIR = Path.home() / ".cache" / "huggingface"
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(CACHE_DIR))
os.environ.setdefault("TRANSFORMERS_CACHE", str(CACHE_DIR / "transformers"))

# ==================== Piper 配置 ====================

PIPER_BIN = "piper"

MODEL_SEARCH_PATHS = [
    ".",
    "models",
    "~/.local/share/piper_voices",
    "~/piper_models",
]

ZH_MODEL = "zh_CN-xiao_ya-medium.onnx"
ZH_CONFIG = "zh_CN-xiao_ya-medium.onnx.json"

EN_MODEL = "en_US-amy-medium.onnx"
EN_CONFIG = "en_US-amy-medium.onnx.json"

AUDIO_DIR = Path("data/audio")

# ==================== 中英文混合 TTS 常量 ====================

SENTENCE_SPLIT_RE = re.compile(r'(?<=[。！？!?])')

# ==================== 中英文混合 TTS 工具函数 ====================


QUOTE_RE = re.compile(r'[“"](.+?)[”"]')

EN_RE = re.compile(r'[A-Za-z]{2,}')


def detect_lang(text: str) -> str:
    if EN_RE.search(text):
        return "en"
    return "zh"


def split_mixed_sentence(text: str) -> List[Tuple[str, str]]:
    """
    返回 [(文本, 语言)]
    """
    results = []
    last = 0

    for m in QUOTE_RE.finditer(text):
        start, end = m.span()

        # 引号外（前）
        if start > last:
            outside = text[last:start].strip()
            if outside:
                results.append((outside, "zh"))

        # 引号内
        quoted = m.group(1).strip()
        if quoted:
            results.append((quoted, detect_lang(quoted)))

        last = end

    # 尾部
    if last < len(text):
        tail = text[last:].strip()
        if tail:
            results.append((tail, "zh"))

    return results


def split_sentences(text: str) -> List[str]:
    """按中文标点符号分割句子"""
    text = text.strip()
    parts = SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def is_english_sentence(text: str) -> bool:
    """
    判断是否需要用英文模型
    规则：包含连续 3+ 英文字母（即英文单词）
    """
    return bool(re.search(r'[A-Za-z]{3,}', text))


def concat_wavs(wav_files: List[str], output_path: str):
    """拼接多个 WAV 文件"""
    SAMPLE_RATE = 22050
    CHANNELS = 1
    SAMPLE_WIDTH = 2  # 16bit

    with wave.open(output_path, "wb") as out:
        out.setnchannels(CHANNELS)
        out.setsampwidth(SAMPLE_WIDTH)
        out.setframerate(SAMPLE_RATE)

        for wav in wav_files:
            with wave.open(wav, "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))


# ==================== Piper 单例 ====================

_PIPER_VOICE_ZH = None
_PIPER_VOICE_EN = None
_PIPER_LOCK = threading.Lock()
_PIPER_AVAILABLE = None


def _check_piper_python() -> bool:
    global _PIPER_AVAILABLE
    if _PIPER_AVAILABLE is not None:
        return _PIPER_AVAILABLE
    try:
        from piper import PiperVoice  # noqa
        _PIPER_AVAILABLE = True
    except ImportError:
        _PIPER_AVAILABLE = False
    return _PIPER_AVAILABLE


def _get_piper_voice_zh(model: str, config: str):
    global _PIPER_VOICE_ZH
    if _PIPER_VOICE_ZH is None:
        with _PIPER_LOCK:
            if _PIPER_VOICE_ZH is None:
                from piper import PiperVoice
                print(f"🔊 加载 Piper 模型: {Path(model).name}")
                _PIPER_VOICE_ZH = PiperVoice.load(model, config_path=config)
                print("✅ Piper 模型加载完成")
    return _PIPER_VOICE_ZH


def _get_piper_voice_en(model: str, config: str):
    global _PIPER_VOICE_EN
    if _PIPER_VOICE_EN is None:
        with _PIPER_LOCK:
            if _PIPER_VOICE_EN is None:
                from piper import PiperVoice
                print(f"🔊 加载 Piper 模型: {Path(model).name}")
                _PIPER_VOICE_EN = PiperVoice.load(model, config_path=config)
                print("✅ Piper 模型加载完成")
    return _PIPER_VOICE_EN


def warmup_piper():
    """预热中英文模型，避免首段卡死"""
    if not _check_piper_python():
        return
    try:
        # Warmup 中文模型
        zh_model = find_model_file(ZH_MODEL)
        zh_config = find_model_file(ZH_CONFIG)
        zh_voice = _get_piper_voice_zh(zh_model, zh_config)
        zh_voice.synthesize("今天天气不错。", None)

        # Warmup 英文模型
        en_model = find_model_file(EN_MODEL)
        en_config = find_model_file(EN_CONFIG)
        en_voice = _get_piper_voice_en(en_model, en_config)
        en_voice.synthesize("Hello world.", None)

        print("🔥 Piper 中英文模型预热完成")
    except Exception as e:
        print(f"⚠️ Piper 预热失败: {e}")


# ==================== 模型查找 ====================


def find_model_file(name: str) -> Optional[str]:
    p = Path(name).expanduser()
    if p.is_absolute() and p.exists():
        return str(p)

    for base in MODEL_SEARCH_PATHS:
        base = Path(base).expanduser()
        candidate = base / name
        if candidate.exists():
            return str(candidate)
    return None


def get_piper_models() -> List[str]:
    models = []
    for base in MODEL_SEARCH_PATHS:
        base = Path(base).expanduser()
        if not base.exists():
            continue
        models.extend(str(p) for p in base.glob("*.onnx"))
    return models


# ==================== TTS 核心 ====================


def text_to_speech(
        text: str,
        output_path: str
) -> str:
    """
    中英文混合 TTS - 自动检测并切换模型

    Args:
        text: 输入文本（可包含中英文混合）
        output_path: 输出 WAV 文件路径

    Returns:
        输出文件路径
    """
    text = text.strip()
    if not text:
        raise ValueError("文本为空")

    # 查找模型文件
    zh_model = find_model_file(ZH_MODEL)
    if not zh_model:
        raise FileNotFoundError(f"未找到中文模型: {ZH_MODEL}")
    zh_config = find_model_file(ZH_CONFIG)
    if not zh_config:
        zh_config = find_model_file(Path(zh_model).stem + ".json")
        if not zh_config:
            raise FileNotFoundError("中文模型配置文件缺失")

    en_model = find_model_file(EN_MODEL)
    if not en_model:
        raise FileNotFoundError(f"未找到英文模型: {EN_MODEL}")
    en_config = find_model_file(EN_CONFIG)
    if not en_config:
        en_config = find_model_file(Path(en_model).stem + ".json")
        if not en_config:
            raise FileNotFoundError("英文模型配置文件缺失")

    # 分割句子
    sentences = split_mixed_sentence(text)
    if not sentences:
        raise ValueError("未能分割出有效句子")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if _check_piper_python():
        # 使用 Python API
        return _tts_mixed_python(sentences, output_file, zh_model, zh_config, en_model, en_config)
    else:
        # 使用 subprocess
        return _tts_mixed_subprocess(sentences, output_file, zh_model, zh_config, en_model, en_config)


def _tts_mixed_python(sentences: List[Tuple[str, str]], output: Path,
                      zh_model: str, zh_config: str,
                      en_model: str, en_config: str) -> str:
    """使用 Python API 进行中英文混合 TTS"""
    import wave

    # 加载两个模型
    zh_voice = _get_piper_voice_zh(zh_model, zh_config)
    en_voice = _get_piper_voice_en(en_model, en_config)

    sample_rate = zh_voice.config.sample_rate

    with tempfile.TemporaryDirectory() as tmp:
        temp_wavs = []
        for idx, sent in enumerate(sentences):
            voice = en_voice if sent[1] == 'en' else zh_voice
            wav_path = Path(tmp) / f"{idx:04d}.wav"

            with wave.open(str(wav_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                voice.synthesize_wav(sent[0], wf)

            temp_wavs.append(str(wav_path))

        concat_wavs(temp_wavs, str(output))

    return str(output)


def _tts_mixed_subprocess(sentences: List[Tuple[str, str]], output: Path,
                          zh_model: str, zh_config: str,
                          en_model: str, en_config: str) -> str:
    """使用 subprocess 进行中英文混合 TTS"""
    with tempfile.TemporaryDirectory() as tmp:
        temp_wavs = []
        for idx, sent in enumerate(sentences):
            model = en_model if sent[1] == 'en' else zh_model
            config = en_config if sent[1] == 'en' else zh_config
            wav_path = Path(tmp) / f"{idx:04d}.wav"

            cmd = [
                PIPER_BIN,
                "--model", model,
                "--config", config,
                "-f", str(wav_path),
            ]

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            _, stderr = proc.communicate(sent[0], timeout=300)
            if proc.returncode != 0:
                raise RuntimeError(f"Piper 失败: {stderr}")

            temp_wavs.append(str(wav_path))

        concat_wavs(temp_wavs, str(output))

    return str(output)


# ==================== Chunk 接口（保持你原有结构） ====================


def chunk_to_audio_path(book_id: int, chunk_id: int) -> str:
    return str(AUDIO_DIR / str(book_id) / f"chunk_{chunk_id:05d}.wav")


def convert_chunk(text: str, book_id: int, chunk_id: int) -> str:
    text = text.strip()
    if not text:
        raise ValueError(f"Chunk {chunk_id} 文本为空")

    output = chunk_to_audio_path(book_id, chunk_id)

    try:
        path = text_to_speech(text, output)
        size = Path(path).stat().st_size
        if size == 0:
            raise RuntimeError("音频文件为空")
        print(f"✓ Chunk {chunk_id} OK ({size / 1024:.1f} KB)")
        return path
    except Exception as e:
        print(f"✗ Chunk {chunk_id} 失败: {e}")
        if Path(output).exists():
            Path(output).unlink(missing_ok=True)
        raise


def debug_chunk_content(book_id: int, chunk_id: int) -> dict:
    """
    调试chunk内容，检查文本和音频文件状态

    Args:
        book_id: 书籍 ID
        chunk_id: chunk ID

    Returns:
        调试信息字典
    """
    from novel_reader.core import get_book
    from novel_reader.utils import load_txt_file, parse_txt

    book = get_book(book_id)
    if not book:
        return {"error": "书籍不存在"}

    text = load_txt_file(book['file_path'])
    chunks, chapters = parse_txt(text)

    if chunk_id >= len(chunks):
        return {"error": f"Chunk {chunk_id} 超出范围 (总共 {len(chunks)} 个)"}

    chunk_text = chunks[chunk_id].strip()
    audio_path = chunk_to_audio_path(book_id, chunk_id)

    result = {
        "chunk_id": chunk_id,
        "text_length": len(chunk_text),
        "text_preview": chunk_text[:100] if chunk_text else "",
        "text_empty": len(chunk_text) == 0,
        "audio_path": audio_path,
        "audio_exists": Path(audio_path).exists(),
        "audio_size": Path(audio_path).stat().st_size if Path(audio_path).exists() else 0,
    }

    return result
