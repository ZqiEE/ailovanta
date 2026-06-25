from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_path")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    bundle = json.loads(Path(args.bundle_path).read_text(encoding="utf-8"))
    plan_id = bundle["plan"]["plan_id"]
    items = [{"id": item["task_id"], "source": item} for item in bundle.get("tasks", [])]
    with httpx.Client(timeout=30) as client:
        response = client.post(args.api_url.rstrip("/") + "/parcels/push", json={"group_id": plan_id, "items": items})
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
