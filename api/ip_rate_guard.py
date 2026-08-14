from __future__ import annotations

import os
import threading
from collections import defaultdict, deque
from time import monotonic


class IpRateGuard:
    """Small in-process abuse guard for the zero-cash control plane."""

    def __init__(self, *, prefix: str, default_limit: int, default_window_seconds: int) -> None:
        key = prefix.upper().replace("-", "_")
        self.limit = max(1, int(os.getenv(f"AILOVANTA_{key}_LIMIT", str(default_limit))))
        self.window_seconds = max(
            1, int(os.getenv(f"AILOVANTA_{key}_WINDOW_SECONDS", str(default_window_seconds)))
        )
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

    def policy(self) -> dict[str, int]:
        return {"limit": self.limit, "window_seconds": self.window_seconds}
