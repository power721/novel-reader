"""
配置管理模块 - 管理应用程序设置
"""
import json
from pathlib import Path
from typing import Any

# 配置文件路径
SETTINGS_FILE = Path("data/settings.json")

# 默认配置
DEFAULT_SETTINGS = {
    "auto_play_on_startup": True,  # 启动时自动播放
    "auto_play_on_book_select": False,  # 选择书籍时自动播放
    "remember_last_book": True,  # 记住最后选择的书籍
    "auto_play_next_book": False,  # 自动播放下一本书
    "auto_play_next_chapter": True,  # 自动播放下一章节
    "prefetch_chunk_count": 3,  # 预转换后续chunk数量
    "cleanup_old_chunk_threshold": 50,  # 清理N之前的音频文件
    "volume": 1.0,  # 音量 (0.0 - 1.0)
    "playback_speed": 1.0,  # 播放速度 (0.5 - 2.0)
    # TTS 模型设置
    "chinese_model_id": "xiao_ya",  # 中文 TTS 模型 ID
    "english_model_id": "amy",  # 英文 TTS 模型 ID
    "model_dir": "models",  # 模型存储目录
}


def load_settings() -> dict:
    """
    加载配置文件

    Returns:
        配置字典
    """
    if not SETTINGS_FILE.exists():
        # 创建默认配置
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # 合并默认配置（处理新增的配置项）
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value

        return settings
    except Exception as e:
        print(f"加载配置失败: {e}")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """
    保存配置文件

    Args:
        settings: 配置字典
    """
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        print(f"✓ 配置已保存")
    except Exception as e:
        print(f"保存配置失败: {e}")


def get_setting(key: str, default: Any = None) -> Any:
    """
    获取单个配置项

    Args:
        key: 配置键
        default: 默认值

    Returns:
        配置值
    """
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> None:
    """
    设置单个配置项

    Args:
        key: 配置键
        value: 配置值
    """
    settings = load_settings()
    settings[key] = value
    save_settings(settings)


if __name__ == "__main__":
    print("=" * 60)
    print("配置管理测试")
    print("=" * 60)

    # 测试加载配置
    print("\n[1] 加载配置")
    settings = load_settings()
    print(f"配置文件: {SETTINGS_FILE}")
    print(f"配置项: {json.dumps(settings, indent=2, ensure_ascii=False)}")

    # 测试获取单个配置
    print("\n[2] 获取单个配置")
    auto_play = get_setting("auto_play_on_startup")
    print(f"auto_play_on_startup = {auto_play}")

    # 测试设置配置
    print("\n[3] 设置配置")
    set_setting("test_key", "test_value")
    test_value = get_setting("test_key")
    print(f"test_key = {test_value}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
