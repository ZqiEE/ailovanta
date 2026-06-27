from __future__ import annotations

import argparse
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from typing import Any


def headers() -> dict[str, str]:
    out = {"Content-Type": "application/json"}
    token = os.environ.get("AILOVANTA_NODE_TOKEN")
    if token:
        out["X-Ailovanta-Node-Token"] = token
    return out


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(server.rstrip("/") + path, data=json.dumps(body).encode("utf-8"), headers=headers(), method="POST")
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8"))


def get(server: str, path: str) -> dict[str, Any]:
    req = urllib.request.Request(server.rstrip("/") + path, headers=headers(), method="GET")
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode("utf-8"))


def node_loop(server: str, index: int, duration: int, stats: dict[str, int]) -> None:
    node_id = f"stress-node-{index:04d}"
    profile = {
        "node_id": node_id,
        "device_name": node_id,
        "cpu_threads": random.choice([2, 4, 8, 12]),
        "memory_gb": random.choice([4, 8, 16, 24]),
        "has_gpu": index % 5 == 0,
        "gpu_name": "stress-gpu" if index % 5 == 0 else None,
        "contribution_percent": 30,
    }
    try:
        post(server, "/nodes/register", profile)
        stats["registered"] += 1
    except Exception:
        stats["errors"] += 1
        return
    end = time.time() + duration
    while time.time() < end:
        try:
            post(server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
            stats["heartbeats"] += 1
            try:
                job = get(server, f"/jobs/next?node_id={node_id}").get("job")
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    job = None
                else:
                    raise
            if job:
                post(server, "/jobs/result", {"node_id": node_id, "job_id": job.get("id") or job.get("job_id"), "status": "ok", "output_summary": "stress ok"})
                stats["results"] += 1
        except Exception:
            stats["errors"] += 1
        time.sleep(random.uniform(0.2, 1.2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--nodes", type=int, default=20)
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()
    stats = {"registered": 0, "heartbeats": 0, "results": 0, "errors": 0}
    threads = [threading.Thread(target=node_loop, args=(args.server, i, args.duration, stats), daemon=True) for i in range(args.nodes)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(json.dumps({"ok": True, "stats": stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
