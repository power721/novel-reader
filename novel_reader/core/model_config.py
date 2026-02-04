"""
Piper TTS 模型配置模块

管理所有可用的 Piper TTS 模型定义
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PiperModel:
    """
    Piper TTS 模型定义

    Attributes:
        id: 模型唯一标识符（短名称）
        title: 显示名称（中文/英文）
        language: 语言代码 ("zh", "en")
        model_name: 模型文件名 (例如 "zh_CN-xiao_ya-medium.onnx")
        download_url: HuggingFace 下载 URL 基础路径
        size_mb: 大约大小（MB），用于 UI 显示
    """
    id: str
    title: str
    language: str
    model_name: str
    download_url: str
    size_mb: int

    @property
    def config_name(self) -> str:
        """获取配置文件名"""
        return f"{self.model_name}.json"

    @property
    def model_filename(self) -> str:
        """获取模型文件名"""
        return self.model_name

    def __repr__(self) -> str:
        return f"PiperModel(id={self.id}, title={self.title}, lang={self.language})"


# ==================== 模型注册表 ====================

# HuggingFace 基础 URL
HF_BASE_URL_MAIN = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# 中文模型
ZH_MODELS: List[PiperModel] = [
    PiperModel(
        id="xiao_ya",
        title="小雅 (Xiao Ya)",
        language="zh",
        model_name="zh_CN-xiao_ya-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium",
        size_mb=60
    ),
    PiperModel(
        id="huayan",
        title="花檐 (Hua Yan)",
        language="zh",
        model_name="zh_CN-huayan-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/zh/zh_CN/huayan/medium/zh_CN-huayan-medium",
        size_mb=60
    ),
    PiperModel(
        id="chaowen",
        title="潮文 (Chao Wen)",
        language="zh",
        model_name="zh_CN-chaowen-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/zh/zh_CN/chaowen/medium/zh_CN-chaowen-medium",
        size_mb=60
    ),
]

# 英文模型
EN_MODELS: List[PiperModel] = [
    PiperModel(
        id="amy",
        title="Amy",
        language="en",
        model_name="en_US-amy-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/en/en_US/amy/medium/en_US-amy-medium",
        size_mb=60
    ),
    PiperModel(
        id="lessac",
        title="Lessac",
        language="en",
        model_name="en_US-lessac-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/en/en_US/lessac/medium/en_US-lessac-medium",
        size_mb=60
    ),
    PiperModel(
        id="alan",
        title="Alan",
        language="en",
        model_name="en_GB-alan-medium.onnx",
        download_url=f"{HF_BASE_URL_MAIN}/en/en_GB/alan/medium/en_GB-alan-medium",
        size_mb=60
    ),
]

# 所有模型
ALL_MODELS = ZH_MODELS + EN_MODELS

# 默认模型
DEFAULT_CHINESE_MODEL = "xiao_ya"
DEFAULT_ENGLISH_MODEL = "amy"


# ==================== 查询函数 ====================

def get_model(model_id: str) -> Optional[PiperModel]:
    """
    根据 ID 获取模型

    Args:
        model_id: 模型 ID

    Returns:
        PiperModel 对象，如果未找到返回 None
    """
    for model in ALL_MODELS:
        if model.id == model_id:
            return model
    return None


def get_models_by_language(language: str) -> List[PiperModel]:
    """
    获取指定语言的所有模型

    Args:
        language: 语言代码 ("zh" 或 "en")

    Returns:
        模型列表
    """
    if language == "zh":
        return ZH_MODELS.copy()
    elif language == "en":
        return EN_MODELS.copy()
    return []


def get_default_model(language: str) -> Optional[PiperModel]:
    """
    获取指定语言的默认模型

    Args:
        language: 语言代码 ("zh" 或 "en")

    Returns:
        默认模型，如果未找到返回 None
    """
    if language == "zh":
        return get_model(DEFAULT_CHINESE_MODEL)
    elif language == "en":
        return get_model(DEFAULT_ENGLISH_MODEL)
    return None


def list_model_ids(language: str = None) -> List[str]:
    """
    列出所有模型 ID

    Args:
        language: 可选，过滤指定语言

    Returns:
        模型 ID 列表
    """
    if language:
        models = get_models_by_language(language)
    else:
        models = ALL_MODELS
    return [m.id for m in models]


def get_model_title(model_id: str) -> str:
    """
    获取模型显示标题

    Args:
        model_id: 模型 ID

    Returns:
        显示标题，如果未找到返回 model_id
    """
    model = get_model(model_id)
    if model:
        return model.title
    return model_id


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Piper 模型配置测试")
    print("=" * 60)

    # 测试中文模型
    print("\n[1] 中文模型列表:")
    for model in ZH_MODELS:
        print(f"  - {model.id}: {model.title} ({model.size_mb} MB)")

    # 测试英文模型
    print("\n[2] 英文模型列表:")
    for model in EN_MODELS:
        print(f"  - {model.id}: {model.title} ({model.size_mb} MB)")

    # 测试查询函数
    print("\n[3] 查询测试:")
    xiao_ya = get_model("xiao_ya")
    print(f"  xiao_ya: {xiao_ya}")

    amy = get_model("amy")
    print(f"  amy: {amy}")

    not_found = get_model("not_exist")
    print(f"  not_exist: {not_found}")

    # 测试默认模型
    print("\n[4] 默认模型:")
    print(f"  中文默认: {get_default_model('zh')}")
    print(f"  英文默认: {get_default_model('en')}")

    # 测试按语言查询
    print("\n[5] 按语言查询:")
    zh_models = get_models_by_language("zh")
    print(f"  中文模型数量: {len(zh_models)}")
    en_models = get_models_by_language("en")
    print(f"  英文模型数量: {len(en_models)}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
