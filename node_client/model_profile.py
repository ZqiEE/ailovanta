from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, asdict

import psutil


@dataclass(frozen=True)
class LocalModelProfile:
    model: str
    context_length: int
    reason: str
    gpu_name: str | None
    gpu_memory_gb: float | None
    system_memory_gb: float

    def to_dict(self) -> dict:
        return asdict(self)


def _nvidia_info() -> tuple[str | None, float | None]:
    if not shutil.which("nvidia-smi"):
        return None, None
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except Exception:
        return None, None
    line = next((row.strip() for row in out.splitlines() if row.strip()), "")
    if not line:
        return None, None
    parts = [part.strip() for part in line.rsplit(",", 1)]
    if len(parts) != 2:
        return line, None
    try:
        memory_gb = round(float(parts[1]) / 1024.0, 2)
    except ValueError:
        memory_gb = None
    return parts[0], memory_gb


def recommend_local_model() -> LocalModelProfile:
    """Choose the strongest practical local bootstrap profile for this machine.

    The final Ailovanta-owned checkpoint will replace these bootstrap model tags.
    We keep enough memory headroom for KV cache and the coding workspace instead
    of choosing a model that only barely loads.
    """

    ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    gpu_name, gpu_memory_gb = _nvidia_info()
    is_apple = platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}

    if gpu_memory_gb is not None and gpu_memory_gb >= 22 and ram_gb >= 32:
        return LocalModelProfile(
            model="qwen3-coder:30b",
            context_length=32768,
            reason="22GB+ NVIDIA VRAM and 32GB+ RAM: use the stronger Qwen3-Coder 30B MoE bootstrap",
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory_gb,
            system_memory_gb=ram_gb,
        )
    if gpu_memory_gb is not None and gpu_memory_gb >= 14:
        return LocalModelProfile(
            model="qwen2.5-coder:14b",
            context_length=32768,
            reason="14GB+ NVIDIA VRAM: strong 14B bootstrap with comfortable cache headroom",
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory_gb,
            system_memory_gb=ram_gb,
        )
    if gpu_memory_gb is not None and gpu_memory_gb >= 8:
        return LocalModelProfile(
            model="qwen2.5-coder:7b",
            context_length=24576,
            reason="8GB+ NVIDIA VRAM: balanced 7B local coding profile",
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory_gb,
            system_memory_gb=ram_gb,
        )
    if is_apple and ram_gb >= 48:
        return LocalModelProfile(
            model="qwen3-coder:30b",
            context_length=32768,
            reason="Apple Silicon with 48GB+ unified memory: use the stronger Qwen3-Coder 30B MoE bootstrap",
            gpu_name="Apple Silicon",
            gpu_memory_gb=None,
            system_memory_gb=ram_gb,
        )
    if is_apple and ram_gb >= 24:
        return LocalModelProfile(
            model="qwen2.5-coder:14b",
            context_length=24576,
            reason="Apple Silicon with 24GB+ unified memory: 14B bootstrap profile",
            gpu_name="Apple Silicon",
            gpu_memory_gb=None,
            system_memory_gb=ram_gb,
        )
    if ram_gb >= 16:
        return LocalModelProfile(
            model="qwen2.5-coder:7b",
            context_length=16384,
            reason="16GB+ system memory: 7B bootstrap profile",
            gpu_name=gpu_name,
            gpu_memory_gb=gpu_memory_gb,
            system_memory_gb=ram_gb,
        )
    return LocalModelProfile(
        model="qwen2.5-coder:3b",
        context_length=8192,
        reason="low-memory fallback: keep the product usable without heavy swapping",
        gpu_name=gpu_name,
        gpu_memory_gb=gpu_memory_gb,
        system_memory_gb=ram_gb,
    )
