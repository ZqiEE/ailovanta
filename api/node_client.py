from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import time
import urllib.error
import urllib.request
from typing import Any


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        server.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def get(server: str, path: str) -> dict[str, Any]:
    with urllib.request.urlopen(server.rstrip("/") + path, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def detect(enable_gpu: bool) -> dict[str, Any]:
    memory_gb = 4.0
    try:
        import psutil  # type: ignore
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        pass

    has_gpu = False
    gpu_name = None
    if enable_gpu:
        try:
            import torch  # type: ignore
            has_gpu = bool(torch.cuda.is_available())
            gpu_name = torch.cuda.get_device_name(0) if has_gpu else None
        except Exception:
            pass

    return {
        "device_name": f"{socket.gethostname()}-{platform.system()}",
        "cpu_threads": os.cpu_count() or 1,
        "memory_gb": memory_gb,
        "has_gpu": has_gpu,
        "gpu_name": gpu_name,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument("--node-id", default=None)
    p.add_argument("--contribution-percent", type=int, default=30)
    p.add_argument("--enable-gpu", action="store_true")
    p.add_argument("--interval", type=int, default=10)
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    profile = detect(args.enable_gpu)
    node = post(args.server, "/nodes/register", {**profile, "node_id": args.node_id, "contribution_percent": args.contribution_percent})
    node_id = node["node_id"]
    print(json.dumps({"ok": True, "node": node}, ensure_ascii=False, indent=2))

    while True:
        post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
        try:
            job = get(args.server, f"/jobs/next?node_id={node_id}").get("job")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                job = None
            else:
                raise

        if job:
            post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "busy"})
            summary = f"node finished task on {profile['device_name']}; type={job.get('type') or job.get('job_type')}"
            result = post(args.server, "/jobs/result", {"node_id": node_id, "job_id": job["job_id"], "status": "ok", "output_summary": summary})
            print(json.dumps({"job_id": job["job_id"], "result": result}, ensure_ascii=False, indent=2))
            post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
        elif args.once:
            print(json.dumps({"ok": True, "node_id": node_id, "message": "no job"}, ensure_ascii=False))
            return 0

        if args.once:
            return 0
        time.sleep(max(3, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
