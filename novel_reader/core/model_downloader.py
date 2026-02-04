"""
Piper TTS 模型下载管理模块

负责从 HuggingFace 下载和管理 Piper 模型文件
"""
import os
import urllib.request
from pathlib import Path
from typing import Optional, List, Callable
import hashlib

from .model_config import PiperModel, get_model


# ==================== 配置 ====================

# 模型搜索路径
MODEL_SEARCH_PATHS = [
    "models",
    "~/.local/share/piper_voices",
    "~/piper_models",
    ".",
]

# HuggingFace 镜像（中国用户）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


# ==================== 工具函数 ====================

def get_model_dir() -> Path:
    """
    获取模型存储目录

    优先使用第一个可写目录
    """
    for base in MODEL_SEARCH_PATHS:
        path = Path(base).expanduser()
        # 尝试创建目录
        try:
            path.mkdir(parents=True, exist_ok=True)
            # 测试是否可写
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return path
        except (PermissionError, OSError):
            continue

    # 如果都不可写，使用当前目录的 models 文件夹
    fallback = Path("models")
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def find_model_file(model_name: str) -> Optional[Path]:
    """
    在搜索路径中查找模型文件

    Args:
        model_name: 模型文件名 (例如 "zh_CN-xiao_ya-medium.onnx")

    Returns:
        模型文件路径，如果未找到返回 None
    """
    # 首先检查模型目录
    model_dir = get_model_dir()
    model_path = model_dir / model_name
    if model_path.exists():
        return model_path

    # 然后检查其他搜索路径
    for base in MODEL_SEARCH_PATHS[1:]:  # 跳过第一个，已经检查过了
        path = Path(base).expanduser()
        candidate = path / model_name
        if candidate.exists():
            return candidate

    return None


def get_model_path(model: PiperModel) -> Path:
    """
    获取模型的本地路径

    Args:
        model: PiperModel 对象

    Returns:
        模型文件路径
    """
    model_dir = get_model_dir()
    return model_dir / model.model_filename


def get_model_config_path(model: PiperModel) -> Path:
    """
    获取模型配置文件的本地路径

    Args:
        model: PiperModel 对象

    Returns:
        配置文件路径
    """
    model_dir = get_model_dir()
    return model_dir / model.config_name


def calculate_file_hash(file_path: Path) -> str:
    """
    计算文件的 SHA256 哈希值

    Args:
        file_path: 文件路径

    Returns:
        十六进制哈希值
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 分块读取文件以处理大文件
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ==================== 模型下载器 ====================

class ModelDownloader:
    """
    模型下载器

    支持从 HuggingFace 下载 Piper 模型文件
    """

    def __init__(self, model: PiperModel):
        """
        初始化下载器

        Args:
            model: 要下载的模型
        """
        self.model = model
        self.model_path = get_model_path(model)
        self.config_path = get_model_config_path(model)

    def is_model_available(self) -> bool:
        """
        检查模型是否已下载

        Returns:
            是否已下载（包括 .onnx 和 .json 文件）
        """
        return self.model_path.exists() and self.config_path.exists()

    def get_download_urls(self) -> tuple:
        """
        获取下载 URL

        Returns:
            (model_url, config_url)
        """
        base_url = self.model.download_url
        model_url = f"{base_url}.onnx"
        config_url = f"{base_url}.onnx.json"
        return model_url, config_url

    def download(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
        """
        下载模型文件（包括 .onnx 和 .json）

        Args:
            progress_callback: 进度回调函数 (filename, current_bytes, total_bytes)

        Returns:
            是否下载成功
        """
        model_dir = get_model_dir()
        model_dir.mkdir(parents=True, exist_ok=True)

        model_url, config_url = self.get_download_urls()
        print(model_url)

        # 下载模型文件
        if not self._download_file(model_url, self.model_path, progress_callback):
            return False

        # 下载配置文件
        if not self._download_file(config_url, self.config_path, progress_callback):
            # 清理已下载的模型文件
            if self.model_path.exists():
                self.model_path.unlink()
            return False

        return True

    def _download_file(self, url: str, dest_path: Path,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
        """
        下载单个文件

        Args:
            url: 下载 URL
            dest_path: 目标路径
            progress_callback: 进度回调函数

        Returns:
            是否下载成功
        """
        try:
            print(f"📥 下载中: {dest_path.name}")

            def hook(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    progress_callback(dest_path.name, block_num * block_size, total_size)

            # 使用 urllib.request 下载（支持进度回调）
            urllib.request.urlretrieve(url, dest_path, reporthook=hook)

            # 验证文件大小
            file_size = dest_path.stat().st_size
            if file_size < 1000:  # 小于 1KB 认为是错误页面
                print(f"✗ 下载失败: 文件过小 ({file_size} bytes)")
                dest_path.unlink()
                return False

            print(f"✓ 下载完成: {dest_path.name} ({file_size / 1024 / 1024:.2f} MB)")
            return True

        except Exception as e:
            print(f"✗ 下载失败: {dest_path.name} - {e}")
            if dest_path.exists():
                dest_path.unlink()
            return False

    def delete(self) -> bool:
        """
        删除模型文件

        Returns:
            是否删除成功
        """
        success = True

        # 删除模型文件
        if self.model_path.exists():
            try:
                self.model_path.unlink()
                print(f"✓ 已删除: {self.model_path.name}")
            except Exception as e:
                print(f"✗ 删除失败: {self.model_path.name} - {e}")
                success = False

        # 删除配置文件
        if self.config_path.exists():
            try:
                self.config_path.unlink()
                print(f"✓ 已删除: {self.config_path.name}")
            except Exception as e:
                print(f"✗ 删除失败: {self.config_path.name} - {e}")
                success = False

        return success


# ==================== 批量操作 ====================

def get_available_models() -> List[PiperModel]:
    """
    获取所有已下载的模型

    Returns:
        已下载的模型列表
    """
    from .model_config import ALL_MODELS

    available = []
    for model in ALL_MODELS:
        downloader = ModelDownloader(model)
        if downloader.is_model_available():
            available.append(model)

    return available


def get_missing_models() -> List[PiperModel]:
    """
    获取所有未下载的模型

    Returns:
        未下载的模型列表
    """
    from .model_config import ALL_MODELS

    missing = []
    for model in ALL_MODELS:
        downloader = ModelDownloader(model)
        if not downloader.is_model_available():
            missing.append(model)

    return missing


def get_model_status(model_id: str) -> dict:
    """
    获取模型状态

    Args:
        model_id: 模型 ID

    Returns:
        状态字典
    """
    model = get_model(model_id)
    if not model:
        return {
            "id": model_id,
            "exists": False,
            "error": "模型未定义"
        }

    downloader = ModelDownloader(model)
    is_available = downloader.is_model_available()

    result = {
        "id": model.id,
        "title": model.title,
        "language": model.language,
        "exists": is_available,
        "model_path": str(downloader.model_path),
        "config_path": str(downloader.config_path),
        "size_mb": model.size_mb,
    }

    # 如果已下载，获取实际文件大小
    if is_available:
        result["model_size_mb"] = downloader.model_path.stat().st_size / 1024 / 1024

    return result


def download_model(model_id: str,
                  progress_callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
    """
    下载指定模型

    Args:
        model_id: 模型 ID
        progress_callback: 进度回调函数

    Returns:
        是否下载成功
    """
    model = get_model(model_id)
    if not model:
        print(f"✗ 未找到模型: {model_id}")
        return False

    downloader = ModelDownloader(model)
    if downloader.is_model_available():
        print(f"✓ 模型已存在: {model.title}")
        return True

    print(f"📥 开始下载模型: {model.title}")
    success = downloader.download(progress_callback)

    if success:
        print(f"✅ 模型下载完成: {model.title}")
    else:
        print(f"❌ 模型下载失败: {model.title}")

    return success


def delete_model(model_id: str) -> bool:
    """
    删除指定模型

    Args:
        model_id: 模型 ID

    Returns:
        是否删除成功
    """
    model = get_model(model_id)
    if not model:
        print(f"✗ 未找到模型: {model_id}")
        return False

    downloader = ModelDownloader(model)
    if not downloader.is_model_available():
        print(f"✗ 模型未下载: {model.title}")
        return False

    print(f"🗑 删除模型: {model.title}")
    return downloader.delete()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("模型下载器测试")
    print("=" * 60)

    # 测试获取模型目录
    print("\n[1] 模型目录:")
    model_dir = get_model_dir()
    print(f"  {model_dir}")

    # 测试已下载的模型
    print("\n[2] 已下载的模型:")
    available = get_available_models()
    if available:
        for model in available:
            print(f"  - {model.id}: {model.title}")
    else:
        print("  (无)")

    # 测试未下载的模型
    print("\n[3] 未下载的模型:")
    missing = get_missing_models()
    if missing:
        for model in missing[:5]:  # 只显示前5个
            print(f"  - {model.id}: {model.title} ({model.size_mb} MB)")
        if len(missing) > 5:
            print(f"  ... 还有 {len(missing) - 5} 个")
    else:
        print("  (全部已下载)")

    # 测试模型状态
    print("\n[4] 模型状态测试:")
    for model_id in ["xiao_ya", "amy", "not_exist"]:
        status = get_model_status(model_id)
        if status.get("error"):
            print(f"  {model_id}: {status['error']}")
        else:
            exists = "✓" if status["exists"] else "✗"
            print(f"  {model_id}: {exists} {status['title']}")

    # 测试查找文件
    print("\n[5] 查找文件测试:")
    test_files = [
        "zh_CN-xiao_ya-medium.onnx",
        "en_US-amy-medium.onnx",
        "not_exist.onnx"
    ]
    for filename in test_files:
        path = find_model_file(filename)
        if path:
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"  {filename}: ✓ ({size_mb:.2f} MB)")
        else:
            print(f"  {filename}: ✗")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
