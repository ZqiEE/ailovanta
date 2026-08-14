from __future__ import annotations

import os
import threading
from collections import defaultdict, deque
from time import monotonic


class LocalUsageGuard:
    """Single-process rate + concurrency guard with no external service.

    Ailovanta Coding intentionally runs one API process in the zero-cash setup,
    so a local guard is enough to protect the expensive model endpoint without
    requiring Redis or another managed dependency.
    """

    def __init__(self) -> None:
        self.window_seconds = max(1, int(os.getenv("AILOVANTA_PROPOSE_WINDOW_SECONDS", "60")))
        self.limit = max(1, int(os.getenv("AILOVANTA_PROPOSES_PER_WINDOW", "12")))
        self.acquire_timeout = max(0.0, float(os.getenv("AILOVANTA_MODEL_QUEUE_TIMEOUT_SECONDS", "1.5")))
        concurrency = max(1, int(os.getenv("AILOVANTA_MODEL_CONCURRENCY", "1")))
        self._model_slots = threading.BoundedSemaphore(concurrency)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True

    def acquire_model(self) -> bool:
        return self._model_slots.acquire(timeout=self.acquire_timeout)

    def release_model(self) -> None:
        self._model_slots.release()

    def policy(self) -> dict[str, int | float]:
        return {
            "proposes_per_window": self.limit,
            "window_seconds": self.window_seconds,
            "model_queue_timeout_seconds": self.acquire_timeout,
            "model_concurrency": int(os.getenv("AILOVANTA_MODEL_CONCURRENCY", "1")),
        }
