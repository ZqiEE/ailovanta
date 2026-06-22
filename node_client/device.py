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

    def to_api_payload(self, contribution_percent: int) -> dict:
        payload = asdict(self)
        payload["contribution_percent"] = contribution_percent
        return payload


def detect_device() -> DeviceProfile:
    gpu_name = detect_nvidia_gpu()
    return DeviceProfile(
        device_name=platform.node() or "local-node",
        os=f"{platform.system()} {platform.release()}",
        cpu_threads=psutil.cpu_count(logical=True) or 1,
        memory_gb=round(psutil.virtual_memory().total / (1024**3), 2),
        has_gpu=bool(gpu_name),
        gpu_name=gpu_name,
        gpu_backend="nvidia-smi" if gpu_name else None,
    )


def detect_nvidia_gpu() -> str | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    names = [line.strip() for line in output.splitlines() if line.strip()]
    return names[0] if names else None
