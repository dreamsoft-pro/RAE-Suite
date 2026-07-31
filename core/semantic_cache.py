"""
RAE-Suite Hardened Cache-Aside & Semantic Watchdog
Includes:
1. Singleflight (request coalescing to prevent thundering herd).
2. TTL Jitter (base_ttl * random(0.85, 1.15)).
3. Negative caching for deterministic rejections.
4. Semantic Watchdog (detects non-improving repair loops / semantic stagnation).
"""

import time
import random
import hashlib
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field


class CacheEntryKind(str, Enum):
    VALUE = "VALUE"
    NEGATIVE = "NEGATIVE"


class CacheEntry(BaseModel):
    kind: CacheEntryKind
    key: str
    value: Any
    fresh_until: float
    stale_until: float


class SemanticWatchdog:
    """
    Detects semantic loops (e.g. Phoenix patch generation stagnation without quality score improvement).
    """
    def __init__(self, max_stagnant_cycles: int = 3):
        self.max_stagnant_cycles = max_stagnant_cycles
        self._history: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def record_score_and_check_stagnation(self, loop_id: str, quality_score: float) -> tuple[bool, str]:
        """
        Records quality score. If quality score has not improved for max_stagnant_cycles,
        returns (True, "SEMANTIC_LOOP_DETECTED").
        """
        with self._lock:
            scores = self._history.setdefault(loop_id, [])
            scores.append(quality_score)

            if len(scores) >= self.max_stagnant_cycles:
                recent = scores[-self.max_stagnant_cycles:]
                # If max score in recent window hasn't improved over first score in window
                if max(recent) <= recent[0]:
                    return True, f"SEMANTIC_LOOP_DETECTED: Quality score stagnant at {quality_score:.2f} for {self.max_stagnant_cycles} cycles"

            return False, "OK"


class HardenedSemanticCache:
    """
    Cache-Aside implementation featuring Singleflight request coalescing,
    TTL Jitter, and Negative Caching.
    """
    def __init__(self, base_ttl_s: float = 60.0, jitter_ratio: float = 0.15):
        self.base_ttl_s = base_ttl_s
        self.jitter_ratio = jitter_ratio
        self._cache: Dict[str, CacheEntry] = {}
        self._singleflight_locks: Dict[str, threading.Lock()] = {}
        self._lock = threading.Lock()

    def _compute_jittered_ttl(self) -> float:
        min_mult = 1.0 - self.jitter_ratio
        max_mult = 1.0 + self.jitter_ratio
        return self.base_ttl_s * random.uniform(min_mult, max_mult)

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any], is_negative: bool = False) -> Any:
        """
        Gets value from cache or computes it under Singleflight request coalescing lock.
        """
        now = time.time()

        with self._lock:
            entry = self._cache.get(key)
            if entry and entry.fresh_until > now:
                return entry.value

            # Get or create singleflight lock per key
            sf_lock = self._singleflight_locks.setdefault(key, threading.Lock())

        # Singleflight execution
        with sf_lock:
            # Re-check cache inside lock
            with self._lock:
                entry = self._cache.get(key)
                if entry and entry.fresh_until > now:
                    return entry.value

            # Compute value
            val = compute_fn()
            ttl = self._compute_jittered_ttl()

            with self._lock:
                self._cache[key] = CacheEntry(
                    kind=CacheEntryKind.NEGATIVE if is_negative else CacheEntryKind.VALUE,
                    key=key,
                    value=val,
                    fresh_until=now + ttl,
                    stale_until=now + (ttl * 2)
                )
                self._singleflight_locks.pop(key, None)

            return val
