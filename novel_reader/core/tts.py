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
import subprocess
import threading
from pathlib import Path
from typing import Optional, List

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

DEFAULT_MODEL = "zh_CN-xiao_ya-medium.onnx"
DEFAULT_CONFIG = "zh_CN-xiao_ya-medium.onnx.json"

AUDIO_DIR = Path("data/audio")

# ==================== Piper 单例 ====================

_PIPER_VOICE = None
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


def _get_piper_voice(model: str, config: str):
    global _PIPER_VOICE
    if _PIPER_VOICE is None:
        with _PIPER_LOCK:
            if _PIPER_VOICE is None:
                from piper import PiperVoice
                print(f"🔊 加载 Piper 模型: {Path(model).name}")
                _PIPER_VOICE = PiperVoice.load(model, config_path=config)
                print("✅ Piper 模型加载完成")
    return _PIPER_VOICE


def warmup_piper(model: str, config: str):
    """预热模型，避免首段卡死"""
    if not _check_piper_python():
        return
    try:
        voice = _get_piper_voice(model, config)
        voice.synthesize("测试", None)
        print("🔥 Piper 模型预热完成")
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
        output_path: str,
        model: Optional[str] = None,
        config: Optional[str] = None,
) -> str:
    text = text.strip()
    if not text:
        raise ValueError("文本为空")

    model = model or DEFAULT_MODEL
    config = config or DEFAULT_CONFIG

    model_path = find_model_file(model)
    if not model_path:
        models = get_piper_models()
        if not models:
            raise FileNotFoundError("未找到任何 Piper 模型")
        model_path = models[0]
        print(f"⚠️ 使用自动检测模型: {Path(model_path).name}")

    config_path = find_model_file(config)
    if not config_path:
        alt = find_model_file(Path(model_path).stem + ".json")
        if not alt:
            raise FileNotFoundError("模型配置文件缺失")
        config_path = alt

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if _check_piper_python():
        return _tts_python(text, output_file, model_path, config_path)
    else:
        return _tts_subprocess(text, output_file, model_path, config_path)


def _tts_python(text: str, output: Path, model: str, config: str) -> str:
    import wave

    voice = _get_piper_voice(model, config)

    with wave.open(str(output), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(voice.config.sample_rate)
        voice.synthesize_wav(text, wf)

    return str(output)


def _tts_subprocess(text: str, output: Path, model: str, config: str) -> str:
    cmd = [
        PIPER_BIN,
        "--model",
        model,
        "--config",
        config,
        "-f",
        str(output),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _, stderr = proc.communicate(text, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(stderr)

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
