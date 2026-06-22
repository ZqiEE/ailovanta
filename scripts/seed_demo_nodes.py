from __future__ import annotations

import argparse

import httpx


DEMO_NODES = [
    {"node_id": "node_demo_cpu_small", "device_name": "cpu-small", "cpu_threads": 4, "memory_gb": 8, "has_gpu": False, "gpu_name": None, "contribution_percent": 25},
    {"node_id": "node_demo_cpu_large", "device_name": "cpu-large", "cpu_threads": 16, "memory_gb": 32, "has_gpu": False, "gpu_name": None, "contribution_percent": 40},
    {"node_id": "node_demo_gpu_mid", "device_name": "gpu-mid", "cpu_threads": 12, "memory_gb": 24, "has_gpu": True, "gpu_name": "demo-gpu-mid", "contribution_percent": 35},
    {"node_id": "node_demo_gpu_large", "device_name": "gpu-large", "cpu_threads": 24, "memory_gb": 64, "has_gpu": True, "gpu_name": "demo-gpu-large", "contribution_percent": 50},
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo nodes for dashboard and reputation testing")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        for node in DEMO_NODES:
            response = client.post(f"{api}/nodes/register", json=node)
            response.raise_for_status()
            print(response.json())
        leaderboard = client.get(f"{api}/reputation/leaderboard")
        leaderboard.raise_for_status()
        print("leaderboard:", leaderboard.json())


if __name__ == "__main__":
    main()
