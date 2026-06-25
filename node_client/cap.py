from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from time import time
from typing import Any


@dataclass
class Accel:
    name: str
    mem_total_gb: float
    mem_free_gb: float
    backend: str = "nvidia-smi"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Cap:
    accel: Accel | None
    engines: list[str] = field(default_factory=list)
    cached_models: list[str] = field(default_factory=list)
    cached_adapters: list[str] = field(default_factory=list)
    region: str = "global"
    load: float = 0.0
    price: float = 0.0
    latency_ms: int = 1000
    ts: float = field(default_factory=lambda: round(time(), 3))

    @property
    def pool(self) -> str:
        if self.accel is None:
            return "cpu_pool"
        if self.accel.mem_total_gb >= 24:
            return "large_gpu_pool"
        return "small_gpu_pool"

    def runtime(self, runtime_id: str, node_id: str, trust: float = 0.5) -> dict[str, Any]:
        return {
            "runtime_id": runtime_id,
            "node_id": node_id,
            "pool": self.pool,
            "region": self.region,
            "status": "online",
            "gpu_memory_gb": self.accel.mem_total_gb if self.accel else 0.0,
            "available_gpu_memory_gb": self.accel.mem_free_gb if self.accel else 0.0,
            "trust_score": trust,
            "current_load": self.load,
            "price_per_1k_tokens": self.price,
            "latency_ms": self.latency_ms,
            "supported_engines": self.engines,
            "cached_models": self.cached_models,
            "cached_adapters": self.cached_adapters,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"accel": self.accel.to_dict() if self.accel else None, "pool": self.pool, "engines": self.engines, "cached_models": self.cached_models, "cached_adapters": self.cached_adapters, "region": self.region, "load": self.load, "price": self.price, "latency_ms": self.latency_ms, "ts": self.ts}


def detect_accel() -> Accel | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"], stderr=subprocess.DEVNULL, text=True, timeout=3)
    except Exception:
        return None
    rows = [line.strip() for line in out.splitlines() if line.strip()]
    if not rows:
        return None
    parts = [part.strip() for part in rows[0].split(",")]
    if len(parts) < 3:
        return None
    return Accel(parts[0], round(float(parts[1]) / 1024, 2), round(float(parts[2]) / 1024, 2))


def detect(region: str = "global", engines: list[str] | None = None, cached_models: list[str] | None = None, cached_adapters: list[str] | None = None) -> Cap:
    return Cap(detect_accel(), engines or ["python", "local"], cached_models or [], cached_adapters or [], region)
