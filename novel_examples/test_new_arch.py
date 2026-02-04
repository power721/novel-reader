#!/usr/bin/env python3
"""
测试新的播放器架构

验证各个组件是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '.')

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("📦 测试模块导入")
    print("=" * 60)

    try:
        from novel_reader.core.models_v2 import (
            TextChunk, Chapter, Book, PlaybackState,
            PlayerConfig, TTSConfig
        )
        print("✓ models_v2 imported")

        from novel_reader.core.chunk_manager_v2 import ChunkManager
        print("✓ chunk_manager_v2 imported")

        from novel_reader.core.audio_cache import AudioCache
        print("✓ audio_cache imported")

        from novel_reader.core.audio_player_v2 import AudioPlayer, QtAudioPlayer
        print("✓ audio_player_v2 imported")

        from novel_reader.core.tts_scheduler_v2 import TTSScheduler
        print("✓ tts_scheduler_v2 imported")

        from novel_reader.core.playback_controller_v2 import PlaybackController
        print("✓ playback_controller_v2 imported")

        print("\n✅ 所有模块导入成功!")

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return False

    return True


def test_chunk_manager():
    """测试ChunkManager"""
    print("\n" + "=" * 60)
    print("🧪 测试 ChunkManager")
    print("=" * 60)

    from novel_reader.core.chunk_manager_v2 import ChunkManager

    manager = ChunkManager()

    # 创建测试文本
    test_text = """
第一章 测试章节

这是一个测试文本。用于验证章节识别和chunk切分功能。

这句话也应该被正确切分。

第二章 第二个章节

这是第二章的内容。我们继续测试chunk切分功能。

最后一句话。
""".strip()

    # 模拟文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_text)
        temp_path = f.name

    try:
        # 解析书籍
        book = manager.parse_book(temp_path, book_id=1)

        # 显示结果
        print(f"\n✓ 书籍解析成功:")
        print(f"  - 标题: {book.title}")
        print(f"  - 章节数: {book.total_chapters}")
        print(f"  - 总chunks: {book.total_chunks}")

        print(f"\n📖 章节列表:")
        for chapter in book.chapters:
            print(f"  {chapter.chapter_id + 1}. {chapter.title}")
            print(f"     chunks: {chapter.chunk_count}")
            for i, chunk in enumerate(chapter.chunks[:3]):  # 只显示前3个chunk
                print(f"       - Chunk {i}: {chunk.text[:30]}...")

        print("\n✅ ChunkManager 测试通过!")
        return True

    finally:
        # 清理
        Path(temp_path).unlink(missing_ok=True)


def test_audio_cache():
    """测试AudioCache"""
    print("\n" + "=" * 60)
    print("🧪 测试 AudioCache")
    print("=" * 60)

    from novel_reader.core.audio_cache import AudioCache

    cache = AudioCache(max_size=5)

    # 测试缓存
    cache.put("key1", "/path/to/audio1.wav", 1000)
    print("✓ 添加缓存项 key1")

    cache.put("key2", "/path/to/audio2.wav", 2000)
    print("✓ 添加缓存项 key2")

    # 测试获取
    result = cache.get("key1")
    if result:
        print(f"✓ 获取缓存 key1: {result}")
    else:
        print("✗ 获取缓存 key1 失败")

    # 测试未命中
    result = cache.get("key3")
    if result is None:
        print("✓ 未命中缓存 key3 (预期行为)")

    # 测试LRU
    for i in range(10):
        cache.put(f"key{i}", f"/path/to/audio{i}.wav", i * 100)

    print(f"✓ 添加10个缓存项")
    print(f"✓ 缓存大小: {cache.size} (最大: {cache.max_size})")
    print(f"✓ 命中率: {cache.hit_rate:.1f}%")

    print("\n✅ AudioCache 测试通过!")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 新架构测试套件")
    print("=" * 60)

    all_passed = True

    # 测试导入
    if not test_imports():
        all_passed = False

    # 测试ChunkManager
    if all_passed:
        if not test_chunk_manager():
            all_passed = False

    # 测试AudioCache
    if all_passed:
        if not test_audio_cache():
            all_passed = False

    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
