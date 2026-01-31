"""
AudioCache - 音频文件缓存（LRU策略）

Production级实现：
- LRU缓存策略
- 磁盘持久化
- 自动清理无效缓存
- 缓存统计
"""
from pathlib import Path
from collections import OrderedDict
from typing import Optional, Tuple
import pickle
import time


class AudioCache:
    """
    音频缓存 - LRU策略

    缓存结构：
    - key: hash(text + model + voice + speed)
    - value: (audio_path, duration_ms, timestamp)
    """

    def __init__(self, max_size: int = 80):
        """
        初始化缓存

        Args:
            max_size: 最大缓存项数
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.cache_file = Path("data/audio_cache.pkl")

        # 统计
        self.hits = 0
        self.misses = 0

        # 尝试加载缓存
        self._load()

    def get(self, key: str) -> Optional[Tuple[str, int]]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            (audio_path, duration_ms) 或 None
        """
        if key in self.cache:
            # 移到末尾（标记为最近使用）
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hits += 1
            return (value[0], value[1])

        self.misses += 1
        return None

    def put(self, key: str, audio_path: str, duration_ms: int):
        """
        添加缓存

        Args:
            key: 缓存键
            audio_path: 音频文件路径
            duration_ms: 音频时长（毫秒）
        """
        # 如果已存在，先删除
        if key in self.cache:
            del self.cache[key]

        # 添加到末尾
        self.cache[key] = (audio_path, duration_ms, time.time())

        # 如果超出大小，删除最旧的
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def contains(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self.cache

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self._save()

    def remove(self, key: str):
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]

    def cleanup(self, audio_dir: Path):
        """
        清理不存在的音频文件

        Args:
            audio_dir: 音频目录
        """
        to_remove = []
        for key, (audio_path, _, _) in self.cache.items():
            if not Path(audio_path).exists():
                to_remove.append(key)

        for key in to_remove:
            del self.cache[key]

        if to_remove:
            print(f"[AudioCache] 🧹 Removed {len(to_remove)} invalid cache entries")

    def _save(self):
        """保存缓存到磁盘"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"[AudioCache] ⚠ Failed to save cache: {e}")

    def _load(self):
        """从磁盘加载缓存"""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)
            print(f"[AudioCache] ✓ Loaded {len(self.cache)} cache entries")
        except Exception as e:
            print(f"[AudioCache] ⚠ Failed to load cache: {e}")
            self.cache = OrderedDict()

    @property
    def size(self) -> int:
        """缓存大小"""
        return len(self.cache)

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def __len__(self) -> int:
        return len(self.cache)

    def __repr__(self) -> str:
        hit_rate = self.hit_rate
        return f"AudioCache(size={len(self.cache)}/{self.max_size}, hit_rate={hit_rate:.1f}%)"
