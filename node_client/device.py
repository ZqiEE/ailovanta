from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass, asdict

import psutil


@dataclass
class DeviceProfile:
    device_name: str
    os: str
    cpu_threads: int
    memory_gb: float
    has_gpu: bool
    gpu_name: str | None
    gpu_backend: str | None
    gpu_memory_gb: float | None = None

    def to_api_payload(self, contribution_percent: int) -> dict:
        payload = asdict(self)
        payload["contribution_percent"] = contribution_percent
        return payload


def detect_device() -> DeviceProfile:
    gpu_name, gpu_memory_gb = detect_nvidia_gpu()
    is_apple = platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}
    if not gpu_name and is_apple:
        gpu_name = "Apple Silicon"
    return DeviceProfile(
        device_name=platform.node() or "local-node",
        os=f"{platform.system()} {platform.release()}",
        cpu_threads=psutil.cpu_count(logical=True) or 1,
        memory_gb=round(psutil.virtual_memory().total / (1024**3), 2),
        has_gpu=bool(gpu_name),
        gpu_name=gpu_name,
        gpu_backend="metal" if is_apple else ("nvidia-smi" if gpu_name else None),
        gpu_memory_gb=gpu_memory_gb,
    )


def detect_nvidia_gpu() -> tuple[str | None, float | None]:
    if not shutil.which("nvidia-smi"):
        return None, None
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except Exception:
        return None, None
    line = next((row.strip() for row in output.splitlines() if row.strip()), "")
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
