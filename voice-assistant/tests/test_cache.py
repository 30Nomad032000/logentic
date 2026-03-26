"""
Tests for the response caching module.
Covers LRUCache, CacheStats, CacheEntry, ResponseCache, and singleton.
"""

import time
import pytest
from src.cache.response_cache import (
    LRUCache, CacheEntry, CacheStats, ResponseCache, get_cache,
)
import src.cache.response_cache as cache_module


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_default_values(self):
        entry = CacheEntry(value="hello", timestamp=1000.0)
        assert entry.value == "hello"
        assert entry.timestamp == 1000.0
        assert entry.hits == 0
        assert entry.size_bytes == 0

    def test_custom_values(self):
        entry = CacheEntry(value=42, timestamp=999.9, hits=5, size_bytes=128)
        assert entry.hits == 5
        assert entry.size_bytes == 128


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_defaults(self):
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.expired == 0
        assert stats.total_entries == 0

    def test_hit_rate_zero_total(self):
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        stats = CacheStats(hits=3, misses=7)
        assert stats.hit_rate == 30.0

    def test_hit_rate_all_hits(self):
        stats = CacheStats(hits=10, misses=0)
        assert stats.hit_rate == 100.0

    def test_to_dict(self):
        stats = CacheStats(hits=5, misses=15, evictions=2, expired=1, total_entries=10)
        d = stats.to_dict()
        assert d["hits"] == 5
        assert d["misses"] == 15
        assert d["evictions"] == 2
        assert d["expired"] == 1
        assert d["total_entries"] == 10
        assert d["hit_rate_percent"] == 25.0


class TestLRUCache:
    """Tests for LRUCache."""

    def test_set_and_get(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        assert cache.get("nonexistent") is None

    def test_miss_increments_stats(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.get("miss1")
        cache.get("miss2")
        assert cache.stats.misses == 2

    def test_hit_increments_stats(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.set("k", "v")
        cache.get("k")
        cache.get("k")
        assert cache.stats.hits == 2

    def test_eviction_when_full(self):
        cache = LRUCache(max_size=2, ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts "a"
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.stats.evictions >= 1

    def test_lru_order(self):
        cache = LRUCache(max_size=2, ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # "a" becomes most recently used
        cache.set("c", 3)  # should evict "b", not "a"
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3

    def test_ttl_expiry(self):
        cache = LRUCache(max_size=10, ttl_seconds=0.1)
        cache.set("k", "v")
        assert cache.get("k") == "v"
        time.sleep(0.15)
        assert cache.get("k") is None
        assert cache.stats.expired >= 1

    def test_clear(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.stats.total_entries == 0

    def test_clear_expired(self):
        cache = LRUCache(max_size=10, ttl_seconds=0.1)
        cache.set("expire1", "v1")
        cache.set("expire2", "v2")
        time.sleep(0.15)
        cache.set("fresh", "v3")
        removed = cache.clear_expired()
        assert removed == 2
        assert cache.get("fresh") == "v3"

    def test_update_existing_key(self):
        cache = LRUCache(max_size=10, ttl_seconds=60)
        cache.set("k", "old")
        cache.set("k", "new")
        assert cache.get("k") == "new"
        assert cache.stats.total_entries == 1

    def test_make_key_deterministic(self):
        cache = LRUCache()
        k1 = cache._make_key("hello", "world")
        k2 = cache._make_key("hello", "world")
        k3 = cache._make_key("hello", "earth")
        assert k1 == k2
        assert k1 != k3

    def test_stats_property(self):
        cache = LRUCache(max_size=5)
        cache.set("a", 1)
        cache.set("b", 2)
        stats = cache.stats
        assert stats.total_entries == 2


class TestResponseCache:
    """Tests for the unified ResponseCache."""

    def test_init(self):
        rc = ResponseCache(translation_max=100, tts_max=50, llm_max=200, ttl_seconds=60)
        assert rc is not None

    def test_translation_cache(self):
        rc = ResponseCache()
        assert rc.get_translation("hello", "en", "ml") is None
        rc.set_translation("hello", "en", "ml", "ഹലോ")
        assert rc.get_translation("hello", "en", "ml") == "ഹലോ"

    def test_translation_cache_case_insensitive(self):
        rc = ResponseCache()
        rc.set_translation("Hello World", "en", "ml", "translated")
        assert rc.get_translation("hello world", "en", "ml") == "translated"

    def test_tts_cache(self):
        rc = ResponseCache()
        assert rc.get_tts("hello", "en", "mms") is None
        rc.set_tts("hello", "en", "mms", b"audio_data", size_bytes=100)
        assert rc.get_tts("hello", "en", "mms") == b"audio_data"

    def test_llm_cache(self):
        rc = ResponseCache()
        assert rc.get_llm_response("what is 1+1", "info") is None
        rc.set_llm_response("what is 1+1", "info", "1+1 equals 2.")
        assert rc.get_llm_response("what is 1+1", "info") == "1+1 equals 2."

    def test_get_stats(self):
        rc = ResponseCache()
        rc.set_translation("a", "en", "ml", "b")
        rc.get_translation("a", "en", "ml")
        stats = rc.get_stats()
        assert "translation" in stats
        assert "tts" in stats
        assert "llm" in stats
        assert stats["translation"]["hits"] == 1

    def test_clear_all(self):
        rc = ResponseCache()
        rc.set_translation("a", "en", "ml", "b")
        rc.set_tts("a", "en", "mms", b"data")
        rc.set_llm_response("a", "info", "resp")
        rc.clear()
        assert rc.get_translation("a", "en", "ml") is None
        assert rc.get_tts("a", "en", "mms") is None
        assert rc.get_llm_response("a", "info") is None

    def test_clear_expired(self):
        rc = ResponseCache(ttl_seconds=0.1)
        rc.set_translation("a", "en", "ml", "b")
        time.sleep(0.15)
        result = rc.clear_expired()
        assert result["translation"] >= 1


class TestGetCacheSingleton:
    """Tests for the get_cache singleton function."""

    def test_singleton(self):
        cache_module._cache = None
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2
        cache_module._cache = None  # cleanup
