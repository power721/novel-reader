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
import subprocess
import os
from pathlib import Path
from typing import Optional, List

# ==================== 配置区 ====================

# Piper 可执行文件路径（subprocess 模式）
PIPER_BIN = "piper"

# 模型搜索路径
MODEL_SEARCH_PATHS = [
    ".",  # 当前目录
    "models",  # models 目录
    "~/.local/share/piper_voices",  # Linux 用户目录
    "~/piper_models",  # 用户主目录
]

# TTS 模型路径（.onnx 文件）
# 默认使用中文模型，如果配置的模型未找到，会自动使用找到的第一个模型
PIPER_MODEL = "zh_CN-xiao_ya-medium.onnx"

# 模型配置文件路径
PIPER_CONFIG = "zh_CN-xiao_ya-medium.onnx.json"

# 音频输出目录
AUDIO_DIR = Path("data/audio")


# ================================================

# 自动检测可用的模型
def auto_detect_model() -> tuple[str, str]:
    """
    自动检测可用的模型

    Returns:
        (model_path, config_path): 模型路径和配置路径
    """
    models = get_piper_models()
    if models:
        # 使用第一个找到的模型
        model_path = models[0]
        # 查找对应的配置文件
        config_name = Path(model_path).stem + ".json"
        config_path = find_model_file(config_name)
        if config_path:
            return model_path, config_path
    return None, None


# ================================================

# 检查是否可用 Python API
_PIPER_PYTHON_AVAILABLE = None


def find_model_file(model_name: str) -> Optional[str]:
    """
    在多个路径中查找模型文件

    Args:
        model_name: 模型文件名

    Returns:
        模型文件的完整路径，如果找不到返回 None
    """
    # 首先检查是否已经是绝对路径
    model_path = Path(model_name)
    if model_path.is_absolute() and model_path.exists():
        return str(model_path)

    # 在搜索路径中查找
    for search_path in MODEL_SEARCH_PATHS:
        search_path = Path(search_path).expanduser()
        full_path = search_path / model_name
        if full_path.exists():
            return str(full_path)

    return None


def get_piper_models() -> List[str]:
    """
    获取所有可用的 Piper 模型

    Returns:
        模型文件路径列表
    """
    models = []

    for search_path in MODEL_SEARCH_PATHS:
        search_path = Path(search_path).expanduser()
        if not search_path.exists():
            continue

        # 查找所有 .onnx 文件
        for model_file in search_path.glob("*.onnx"):
            models.append(str(model_file))

    return models


def _check_piper_python() -> bool:
    """检查 piper-tts Python 包是否可用"""
    global _PIPER_PYTHON_AVAILABLE
    if _PIPER_PYTHON_AVAILABLE is not None:
        return _PIPER_PYTHON_AVAILABLE

    try:
        from piper import PiperVoice
        _PIPER_PYTHON_AVAILABLE = True
        return True
    except ImportError as ex:
        print(ex)
        _PIPER_PYTHON_AVAILABLE = False
        return False


def text_to_speech(text: str, output_path: str,
                   model: Optional[str] = None,
                   config: Optional[str] = None) -> str:
    """
    使用 Piper 将文本转换为语音

    Args:
        text: 要转换的文本
        output_path: 输出音频文件路径（.wav）
        model: TTS 模型路径（可选，默认使用配置）
        config: 模型配置文件路径（可选，默认使用配置）

    Returns:
        实际输出的音频文件路径

    Raises:
        FileNotFoundError: 如果 piper 或模型文件不存在
        subprocess.CalledProcessError: 如果转换失败
    """
    # 使用默认配置
    model = model or PIPER_MODEL
    config = config or PIPER_CONFIG

    # 查找模型文件
    model_path = find_model_file(model)
    if model_path is None:
        # 配置的模型未找到，尝试自动检测
        available_models = get_piper_models()
        if available_models:
            # 使用找到的第一个模型
            model_path = available_models[0]
            print(f"⚠️  配置的模型 {model} 未找到，自动使用: {Path(model_path).name}")
        else:
            # 没有任何模型，提供有用的错误信息
            error_msg = f"Piper 模型文件未找到: {model}\n\n"
            error_msg += f"搜索路径:\n"
            for path in MODEL_SEARCH_PATHS:
                error_msg += f"  - {Path(path).expanduser()}\n"

            error_msg += "\n未找到任何模型文件。\n\n"
            error_msg += "请从以下地址下载 Piper 模型:\n"
            error_msg += "https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0\n\n"
            error_msg += "推荐模型:\n"
            error_msg += "  - 英文: en_US-lessac-medium.onnx\n"
            error_msg += "  - 中文: zh_CN-huayan-medium.onnx\n\n"
            error_msg += "下载后请放置在以下任一目录:\n"
            for path in MODEL_SEARCH_PATHS:
                error_msg += f"  - {Path(path).expanduser()}\n"

            raise FileNotFoundError(error_msg)

    # 查找配置文件
    config_path = find_model_file(config)
    if config_path is None:
        # 如果找不到配置文件，尝试使用模型文件名（带 .onnx） + .json
        config_base = Path(model_path).name + ".json"
        config_path = find_model_file(config_base)

        if config_path is None:
            # 再次尝试使用模型文件名（不带 .onnx） + .json
            config_base2 = Path(model_path).stem + ".json"
            config_path = find_model_file(config_base2)

        if config_path is None:
            raise FileNotFoundError(
                f"Piper 配置文件未找到: {config}\n"
                f"请确保与模型文件 {Path(model_path).name} 对应的 .json 文件存在\n"
                f"尝试的配置文件名: {config_base}, {config_base2}"
            )

    # 确保输出目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 优先尝试 Python API
    if _check_piper_python():
        return _text_to_speech_python(text, output_file, model_path, config_path)
    else:
        return _text_to_speech_subprocess(text, output_file, model_path, config_path)


def _text_to_speech_python(text: str, output_file: Path,
                           model: str, config: str) -> str:
    """使用 Piper Python API 进行转换"""
    try:
        import wave
        from piper import PiperVoice

        # 加载模型
        voice = PiperVoice.load(model, config_path=config)

        # 使用 wave 模块打开文件进行转换
        with wave.open(str(output_file), 'wb') as wav_file:
            # 设置音频参数
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16-bit (2 bytes)
            wav_file.setframerate(voice.config.sample_rate)
            voice.synthesize_wav(text, wav_file)

        return str(output_file)

    except Exception as e:
        raise RuntimeError(f"Piper Python API 转换失败: {e}")


def _text_to_speech_subprocess(text: str, output_file: Path,
                               model: str, config: str) -> str:
    """使用 subprocess 调用 piper 命令行工具"""
    # 构建 piper 命令
    # piper --model <model.onnx> --config <config.json> -f <output.wav>
    cmd = [
        PIPER_BIN,
        "--model", model,
        "--config", config,
        "-f", str(output_file)
    ]

    # 调用 piper（通过 stdin 传入文本）
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 发送文本并等待完成
        stdout, stderr = process.communicate(input=text, timeout=300)

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, cmd, stdout, stderr
            )

        return str(output_file)

    except subprocess.TimeoutExpired:
        process.kill()
        raise TimeoutError(f"TTS 转换超时: {output_file}")

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Piper 未找到，请确保已安装 piper\n"
            f"安装方法:\n"
            f"  Python API: pip install piper-tts\n"
            f"  或下载二进制: https://github.com/OHF-Voice/piper1-gpl/releases"
        )


def check_piper_installed() -> bool:
    """
    检查 piper 是否已安装

    Returns:
        True 如果 piper 可用，否则 False
    """
    try:
        result = subprocess.run(
            [PIPER_BIN, "--help"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired) as ex:
        print(ex)
        return False


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


def chunk_to_audio_path(book_id: int, chunk_id: int) -> str:
    """
    生成 chunk 对应的音频文件路径

    Args:
        book_id: 书籍 ID
        chunk_id: 分段 ID

    Returns:
        音频文件路径
    """
    book_dir = AUDIO_DIR / str(book_id)
    return str(book_dir / f"chunk_{chunk_id:05d}.wav")


def convert_chunk(text: str, book_id: int, chunk_id: int) -> str:
    """
    转换单个 chunk 为音频

    Args:
        text: chunk 文本内容
        book_id: 书籍 ID
        chunk_id: chunk ID

    Returns:
        音频文件路径

    Raises:
        ValueError: 如果文本为空
        RuntimeError: 如果转换失败
    """
    # 检查文本是否为空
    text = text.strip()
    if not text:
        raise ValueError(f"Chunk {chunk_id} 文本为空，无法转换")

    output_path = chunk_to_audio_path(book_id, chunk_id)

    try:
        result = text_to_speech(text, output_path)
        # 验证输出文件
        if not Path(output_path).exists():
            raise RuntimeError(f"转换完成但文件不存在: {output_path}")
        file_size = Path(output_path).stat().st_size
        if file_size == 0:
            raise RuntimeError(f"转换完成但文件为空: {output_path}")
        print(f"  ✓ Chunk {chunk_id} 转换成功 ({file_size / 1024:.1f} KB)")
        return result
    except Exception as e:
        print(f"  ✗ Chunk {chunk_id} 转换失败: {e}")
        # 删除可能生成的损坏文件
        if Path(output_path).exists():
            try:
                Path(output_path).unlink()
                print(f"  🗑 已删除损坏文件: {output_path}")
            except:
                pass
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Piper TTS 测试")
    print("=" * 60)

    # 检查 piper 是否安装
    print("\n[1] 检查 Piper 安装...")
    python_api = _check_piper_python()
    cli_available = check_piper_installed()

    if python_api:
        print("✓ Piper Python API 可用 (piper-tts)")
    elif cli_available:
        print("✓ Piper CLI 可用")
    else:
        print("✗ Piper 未安装")
        print(f"\n请安装 Piper:")
        print(f"  方法 1 (推荐): pip install piper-tts")
        print(f"  方法 2: 下载二进制: https://github.com/OHF-Voice/piper1-gpl/releases")
        exit(1)

    # 测试文本转语音
    print("\n[2] 测试文本转语音...")
    test_text = "Hello, this is a test of the text to speech system."

    try:
        output_file = text_to_speech(
            test_text,
            "data/audio/test.wav"
        )
        print(f"✓ 转换成功: {output_file}")

        # 检查文件大小
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"  文件大小: {size} bytes")

    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        exit(1)

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        exit(1)

    # 测试路径生成
    print("\n[3] 测试路径生成...")
    path1 = chunk_to_audio_path(1, 0)
    path2 = chunk_to_audio_path(5, 123)
    print(f"  Book 1, Chunk 0: {path1}")
    print(f"  Book 5, Chunk 123: {path2}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n使用方法:")
    print("""
from novel_reader.core.tts import text_to_speech, convert_chunk

# 方法 1: 直接转换文本
audio_path = text_to_speech("Hello world", "output.wav")

# 方法 2: 转换书籍 chunk
audio_path = convert_chunk(text_content, book_id=1, chunk_id=0)
    """)
