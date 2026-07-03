from __future__ import annotations

import argparse
import json
import socket
import sys
from urllib import request


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Join a local WiFi Ailovanta runtime network")
    parser.add_argument("--coordinator", required=True, help="Coordinator URL, e.g. http://192.168.1.10:8000")
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--worker-port", type=int, default=9001)
    parser.add_argument("--worker-url", default=None)
    parser.add_argument("--secret", default="lan-local-secret")
    parser.add_argument("--gpu-memory-gb", type=float, default=0.0)
    parser.add_argument("--cached-model", action="append", default=["ailovanta-owned:candidate"])
    args = parser.parse_args()

    ip = local_ip()
    node_id = args.node_id or "lan-node-" + ip.replace(".", "-")
    worker_url = args.worker_url or f"http://{ip}:{args.worker_port}"
    payload = {
        "node_id": node_id,
        "runtime_id": args.runtime_id,
        "worker_url": worker_url,
        "secret": args.secret,
        "gpu_memory_gb": args.gpu_memory_gb,
        "trust_score": 0.85,
        "cached_models": args.cached_model,
        "metadata": {"local_ip": ip, "join_script": "scripts/join_lan_node.py"},
    }
    result = post_json(args.coordinator.rstrip("/") + "/lan/nodes/join", payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
