"""Response caching module for the voice assistant pipeline.

Provides LRU caching with TTL for translation, TTS, and LLM responses
to reduce redundant computation and improve latency.
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    value: Any
    timestamp: float
    hits: int = 0
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    total_entries: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expired": self.expired,
            "total_entries": self.total_entries,
            "hit_rate_percent": round(self.hit_rate, 2),
        }


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 500, ttl_seconds: float = 3600):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._stats = CacheStats()

    def _make_key(self, *parts: str) -> str:
        raw = "|".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._stats.expired += 1
                self._stats.misses += 1
                self._stats.total_entries = len(self._cache)
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats.hits += 1
            return entry.value

    def set(self, key: str, value: Any, size_bytes: int = 0) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = CacheEntry(
                    value=value,
                    timestamp=time.time(),
                    size_bytes=size_bytes,
                )
            else:
                # Evict oldest if at capacity
                while len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
                    self._stats.evictions += 1

                self._cache[key] = CacheEntry(
                    value=value,
                    timestamp=time.time(),
                    size_bytes=size_bytes,
                )
            self._stats.total_entries = len(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._stats.total_entries = 0

    def clear_expired(self) -> int:
        now = time.time()
        removed = 0
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if now - v.timestamp > self._ttl
            ]
            for k in expired_keys:
                del self._cache[k]
                removed += 1
            self._stats.expired += removed
            self._stats.total_entries = len(self._cache)
        return removed

    @property
    def stats(self) -> CacheStats:
        with self._lock:
            self._stats.total_entries = len(self._cache)
            return self._stats


class ResponseCache:
    """Unified cache for all pipeline components.

    Provides separate LRU caches for translation, TTS, and LLM responses
    with configurable sizes and TTL.
    """

    def __init__(
        self,
        translation_max: int = 1000,
        tts_max: int = 200,
        llm_max: int = 500,
        ttl_seconds: float = 3600,
    ):
        self._translation_cache = LRUCache(max_size=translation_max, ttl_seconds=ttl_seconds)
        self._tts_cache = LRUCache(max_size=tts_max, ttl_seconds=ttl_seconds)
        self._llm_cache = LRUCache(max_size=llm_max, ttl_seconds=ttl_seconds)
        logger.info(
            "ResponseCache initialized: translation=%d, tts=%d, llm=%d, ttl=%ds",
            translation_max, tts_max, llm_max, int(ttl_seconds),
        )

    # ---- Translation cache ----

    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        key = self._translation_cache._make_key(text.strip().lower(), source_lang, target_lang)
        result = self._translation_cache.get(key)
        if result is not None:
            logger.debug("Translation cache HIT: %s->%s", source_lang, target_lang)
        return result

    def set_translation(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        key = self._translation_cache._make_key(text.strip().lower(), source_lang, target_lang)
        self._translation_cache.set(key, translated, size_bytes=len(translated.encode()))

    # ---- TTS cache ----

    def get_tts(self, text: str, language: str, engine: str = "mms") -> Optional[Any]:
        key = self._tts_cache._make_key(text.strip().lower(), language, engine)
        result = self._tts_cache.get(key)
        if result is not None:
            logger.debug("TTS cache HIT: %s/%s", language, engine)
        return result

    def set_tts(self, text: str, language: str, engine: str, audio_data: Any, size_bytes: int = 0) -> None:
        key = self._tts_cache._make_key(text.strip().lower(), language, engine)
        self._tts_cache.set(key, audio_data, size_bytes=size_bytes)

    # ---- LLM response cache ----

    def get_llm_response(self, text: str, intent: str = "") -> Optional[str]:
        key = self._llm_cache._make_key(text.strip().lower(), intent)
        result = self._llm_cache.get(key)
        if result is not None:
            logger.debug("LLM cache HIT: intent=%s", intent)
        return result

    def set_llm_response(self, text: str, intent: str, response: str) -> None:
        key = self._llm_cache._make_key(text.strip().lower(), intent)
        self._llm_cache.set(key, response, size_bytes=len(response.encode()))

    # ---- Aggregate operations ----

    def get_stats(self) -> dict:
        return {
            "translation": self._translation_cache.stats.to_dict(),
            "tts": self._tts_cache.stats.to_dict(),
            "llm": self._llm_cache.stats.to_dict(),
        }

    def clear(self) -> None:
        self._translation_cache.clear()
        self._tts_cache.clear()
        self._llm_cache.clear()
        logger.info("All caches cleared")

    def clear_expired(self) -> dict:
        return {
            "translation": self._translation_cache.clear_expired(),
            "tts": self._tts_cache.clear_expired(),
            "llm": self._llm_cache.clear_expired(),
        }


# ---- Singleton ----

_cache: Optional[ResponseCache] = None


def get_cache(**kwargs) -> ResponseCache:
    """Get or create the global ResponseCache instance."""
    global _cache
    if _cache is None:
        _cache = ResponseCache(**kwargs)
    return _cache
