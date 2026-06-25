from __future__ import annotations

import argparse
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from node_client.client import heartbeat, register_node, request_with_retry, setup_logging
from node_client.real_runner import JobRunner
from node_client.resource_guard import ResourceGuard, ResourceLimits
from node_client.task_policy import TaskPolicy


@dataclass
class RealNodeConfig:
    api_url: str
    contribution_percent: int
    poll_seconds: int
    max_cpu_percent: int
    min_free_memory_gb: float
    log_dir: Path
    identity_path: Path
    max_payload_bytes: int
    max_runtime_seconds: float
    max_gpu_percent: int = 80
    max_gpu_memory_percent: int = 80
    max_gpu_temperature_c: int = 78
    min_idle_seconds: int = 0
    pause_on_battery: bool = True


def fetch_job(config: RealNodeConfig, node_id: str) -> dict | None:
    response = request_with_retry("GET", f"{config.api_url}/jobs/next", params={"node_id": node_id})
    return response.json().get("job")


def submit_result(config: RealNodeConfig, node_id: str, result: dict) -> None:
    payload = result | {"node_id": node_id}
    request_with_retry("POST", f"{config.api_url}/jobs/result", json=payload)


def limits(config: RealNodeConfig) -> ResourceLimits:
    return ResourceLimits(config.max_cpu_percent, config.min_free_memory_gb, config.max_gpu_percent, config.max_gpu_memory_percent, config.max_gpu_temperature_c, config.min_idle_seconds, config.pause_on_battery)


def loop(config: RealNodeConfig) -> None:
    setup_logging(config.log_dir)
    guard = ResourceGuard(limits(config))
    runner = JobRunner(TaskPolicy.default().__class__(TaskPolicy.default().allowed_job_types, config.max_payload_bytes, config.max_runtime_seconds))
    node_id = register_node(config)  # type: ignore[arg-type]
    while True:
        try:
            heartbeat(config, node_id, "online")  # type: ignore[arg-type]
            ok, reason = guard.can_run_job()
            if not ok:
                logging.info("paused: %s", reason)
                time.sleep(config.poll_seconds)
                continue
            job = fetch_job(config, node_id)
            if not job:
                logging.info("no job")
                time.sleep(config.poll_seconds)
                continue
            heartbeat(config, node_id, "busy")  # type: ignore[arg-type]
            result = asdict(runner.run(job))
            submit_result(config, node_id, result)
            heartbeat(config, node_id, "idle")  # type: ignore[arg-type]
            logging.info("submitted %s %s", result["job_id"], result["status"])
        except KeyboardInterrupt:
            heartbeat(config, node_id, "offline")  # type: ignore[arg-type]
            raise
        except Exception as exc:
            logging.exception("loop error: %s", exc)
            time.sleep(config.poll_seconds)


def main() -> None:
    p = argparse.ArgumentParser(description="Ailovanta real node client")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--contribution", type=int, default=30)
    p.add_argument("--poll-seconds", type=int, default=5)
    p.add_argument("--max-cpu-percent", type=int, default=70)
    p.add_argument("--min-free-memory-gb", type=float, default=1.5)
    p.add_argument("--max-gpu-percent", type=int, default=80)
    p.add_argument("--max-gpu-memory-percent", type=int, default=80)
    p.add_argument("--max-gpu-temperature-c", type=int, default=78)
    p.add_argument("--min-idle-seconds", type=int, default=0)
    p.add_argument("--allow-on-battery", action="store_true")
    p.add_argument("--log-dir", default="runtime_data/logs")
    p.add_argument("--identity-path", default="runtime_data/node_identity.json")
    p.add_argument("--max-payload-bytes", type=int, default=65536)
    p.add_argument("--max-runtime-seconds", type=float, default=120.0)
    args = p.parse_args()
    loop(RealNodeConfig(args.api_url.rstrip("/"), args.contribution, args.poll_seconds, args.max_cpu_percent, args.min_free_memory_gb, Path(args.log_dir), Path(args.identity_path), args.max_payload_bytes, args.max_runtime_seconds, args.max_gpu_percent, args.max_gpu_memory_percent, args.max_gpu_temperature_c, args.min_idle_seconds, not args.allow_on_battery))


if __name__ == "__main__":
    main()
