#!/usr/bin/env python3
"""
测试TTS超时配置
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '.')

def test_timeout_config():
    """测试超时配置"""
    print("=" * 60)
    print("🧪 测试 TTS 超时配置")
    print("=" * 60)

    from novel_reader.core.models_v2 import PlayerConfig

    config = PlayerConfig()

    print("\n1. 默认配置:")
    print(f"   - first_chunk_timeout: {config.first_chunk_timeout} ms ({config.first_chunk_timeout/1000} 秒)")
    print(f"   - tts_timeout: {config.tts_timeout} 秒")

    # 验证超时时间
    if config.first_chunk_timeout >= 60000:
        print(f"\n   ✓ first_chunk_timeout 已增加到 {config.first_chunk_timeout/1000} 秒")
    else:
        print(f"\n   ✗ first_chunk_timeout 仍然太短: {config.first_chunk_timeout/1000} 秒")
        return False

    if config.tts_timeout >= 300:
        print(f"   ✓ tts_timeout 足够长: {config.tts_timeout} 秒")
    else:
        print(f"   ⚠ tts_timeout 可能太短: {config.tts_timeout} 秒")

    print("\n2. 转换为字典:")
    config_dict = config.to_dict()
    if 'first_chunk_timeout' in config_dict:
        print(f"   ✓ first_chunk_timeout 在字典中: {config_dict['first_chunk_timeout']} ms")

    print("\n✅ 超时配置测试通过!")
    return True


def test_main_window_timeout():
    """测试MainWindow中的超时"""
    print("\n" + "=" * 60)
    print("🧪 测试 MainWindow 超时等待")
    print("=" * 60)

    import re

    # 读取main_window.py文件
    main_window_file = Path("novel_reader/gui/main_window.py")
    if not main_window_file.exists():
        print("✗ main_window.py 文件不存在")
        return False

    content = main_window_file.read_text()

    # 查找max_wait = 的行
    max_wait_matches = re.findall(r'max_wait\s*=\s*(\d+)', content)

    if not max_wait_matches:
        print("✗ 未找到 max_wait 配置")
        return False

    print(f"\n1. 找到 {len(max_wait_matches)} 个 max_wait 配置:")

    for i, value in enumerate(max_wait_matches, 1):
        seconds = int(value)
        print(f"   {i}. max_wait = {seconds} 秒")
        if seconds >= 60:
            print(f"      ✓ 超时时间足够长")
        else:
            print(f"      ✗ 超时时间太短，建议至少60秒")

    # 检查是否有60秒的超时
    if any(int(v) >= 60 for v in max_wait_matches):
        print(f"\n2. ✓ 至少有一个超时配置 >= 60 秒")
    else:
        print(f"\n2. ✗ 所有超时配置都 < 60 秒")
        return False

    print("\n✅ MainWindow 超时配置测试通过!")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 TTS 超时配置测试套件")
    print("=" * 60)

    all_passed = True

    # 测试配置
    if not test_timeout_config():
        all_passed = False

    # 测试MainWindow
    if all_passed:
        if not test_main_window_timeout():
            all_passed = False

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
        print("\n📝 修改内容:")
        print("  1. PlayerConfig.first_chunk_timeout: 3000ms → 60000ms (60秒)")
        print("  2. MainWindow._on_first_chunk_ready: max_wait: 3 → 60 秒")
        print("  3. 检查间隔: 0.2秒 → 0.5秒")
        print("\n💡 这样就给了TTS转换足够的时间来生成音频文件")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
