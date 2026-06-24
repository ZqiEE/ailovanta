from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API_URL = os.getenv("AILOVANTA_API_URL", "http://127.0.0.1:8000").rstrip("/")
WORKER_URL = os.getenv("AILOVANTA_DEFAULT_WORKER_URL", "http://127.0.0.1:9001").rstrip("/")


def wait_get(url: str, seconds: int = 30) -> None:
    deadline = time.time() + seconds
    last_error = "not ready"
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=3) as client:
                response = client.get(url)
                if response.status_code < 500:
                    return
        except Exception as exc:
            last_error = str(exc)
        time.sleep(1)
    raise RuntimeError(f"service not ready: {url}: {last_error}")


def run_step(args: list[str]) -> None:
    print("$", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def start_service(args: list[str]) -> subprocess.Popen:
    print("start", " ".join(args))
    return subprocess.Popen(args, cwd=ROOT)


def main() -> int:
    env = os.environ.copy()
    env.setdefault("OLLAMA_MODEL", "ailovanta-owned:candidate")
    env.setdefault("AILOVANTA_DEFAULT_WORKER_URL", WORKER_URL)

    api = start_service([sys.executable, "-m", "uvicorn", "api.main_owned:app", "--host", "127.0.0.1", "--port", "8000"])
    worker = start_service([sys.executable, "-m", "uvicorn", "api.worker:app", "--host", "127.0.0.1", "--port", "9001"])
    processes = [api, worker]

    def stop_all() -> None:
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    try:
        wait_get(API_URL + "/health")
        wait_get(WORKER_URL + "/health")
        run_step([sys.executable, "scripts/register_owned_runtime.py"])
        run_step([sys.executable, "scripts/check_owned_runtime_ready.py"])
        run_step([sys.executable, "scripts/call_owned_chat.py"])
        print("owned runtime stack: ok")
        return 0
    except Exception as exc:
        print("owned runtime stack: failed", exc, file=sys.stderr)
        return 1
    finally:
        if os.getenv("AILOVANTA_KEEP_SERVICES_RUNNING", "false").lower() not in {"1", "true", "yes"}:
            stop_all()


if __name__ == "__main__":
    raise SystemExit(main())
