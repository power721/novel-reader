#!/usr/bin/env python3
"""
Piper TTS 配置测试脚本

检查 Piper TTS 是否正确配置
"""
import sys
from pathlib import Path


def test_piper_import():
    """测试 piper-tts 是否安装"""
    print("=" * 60)
    print("测试 1: 检查 piper-tts 安装")
    print("=" * 60)

    try:
        import piper
        print("✓ piper-tts 已安装")
        print(f"  版本: {getattr(piper, '__version__', '未知')}")
        return True
    except ImportError:
        print("✗ piper-tts 未安装")
        print("\n请运行: pip install piper-tts")
        return False


def test_model_files():
    """测试模型文件是否存在"""
    print("\n" + "=" * 60)
    print("测试 2: 检查模型文件")
    print("=" * 60)

    from novel_reader.core.tts import (
        find_model_file,
        get_piper_models,
        PIPER_MODEL,
        PIPER_CONFIG
    )

    # 查找配置的模型
    print(f"\n配置的模型: {PIPER_MODEL}")
    model_path = find_model_file(PIPER_MODEL)
    if model_path:
        print(f"✓ 模型文件已找到: {model_path}")
    else:
        print(f"✗ 模型文件未找到")

    print(f"\n配置的配置文件: {PIPER_CONFIG}")
    config_path = find_model_file(PIPER_CONFIG)
    if config_path:
        print(f"✓ 配置文件已找到: {config_path}")
    else:
        print(f"✗ 配置文件未找到")

    # 列出所有可用模型
    print("\n扫描可用的模型文件...")
    models = get_piper_models()
    if models:
        print(f"✓ 找到 {len(models)} 个模型文件:")
        for model in models:
            print(f"  - {model}")
    else:
        print("✗ 未找到任何模型文件")
        print("\n请从以下地址下载模型:")
        print("https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0")
        print("\n推荐的英文模型:")
        print("  - en_US-lessac-medium.onnx")
        print("  - en_US-lessac-medium.onnx.json")

    return len(models) > 0


def test_tts_conversion():
    """测试 TTS 转换"""
    print("\n" + "=" * 60)
    print("测试 3: 测试 TTS 转换")
    print("=" * 60)

    from novel_reader.core.tts import (
        find_model_file,
        PIPER_MODEL,
        PIPER_CONFIG
    )

    # 检查模型文件
    model_path = find_model_file(PIPER_MODEL)
    config_path = find_model_file(PIPER_CONFIG)

    if not model_path or not config_path:
        print("✗ 无法测试 TTS 转换：模型文件未找到")
        return False

    try:
        from novel_reader.core.tts import text_to_speech

        # 确保输出目录存在
        output_dir = Path("data/audio/test")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 执行转换
        print("\n正在转换测试文本...")
        output_file = text_to_speech(
            "Hello, this is a test.",
            str(output_dir / "test.wav"),
            model=model_path,
            config=config_path
        )

        print(f"✓ TTS 转换成功: {output_file}")

        # 检查文件大小
        if Path(output_file).exists():
            size = Path(output_file).stat().st_size
            print(f"  文件大小: {size} bytes")
        else:
            print("✗ 输出文件不存在")
            return False

        return True

    except Exception as e:
        print(f"✗ TTS 转换失败: {e}")
        return False


def test_mpv():
    """测试 mpv 播放器"""
    print("\n" + "=" * 60)
    print("测试 4: 检查 mpv 播放器")
    print("=" * 60)

    from novel_reader.core.player import check_mpv_installed

    if check_mpv_installed():
        print("✓ mpv 已安装")
        return True
    else:
        print("✗ mpv 未安装")
        print("\n请运行: sudo apt install mpv")
        return False


def main():
    """运行所有测试"""
    print("\nPiper TTS 配置测试\n")

    results = []

    # 运行测试
    results.append(("piper-tts 安装", test_piper_import()))
    results.append(("模型文件", test_model_files()))

    # 只有当前面的测试通过时才运行后续测试
    if results[0][1] and results[1][1]:
        results.append(("TTS 转换", test_tts_conversion()))
    else:
        results.append(("TTS 转换", False))

    results.append(("mpv 播放器", test_mpv()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！Piper TTS 已正确配置。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请根据上述提示进行配置。")
        print("\n详细配置指南: docs/PIPER_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
