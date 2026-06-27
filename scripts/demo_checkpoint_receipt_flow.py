from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any

from api.artifact_store import file_sha256
from api.wio import signed_result


def call(method: str, server: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(server.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read().decode("utf-8"))


def write_checkpoint(path: Path, name: str, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "ailovanta.checkpoint.v1", "name": name, "version": version, "kind": "checkpoint"}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WIO task -> local checkpoint receipt -> catalog -> notarize -> publish")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--name", default="ailovanta-checkpoint")
    parser.add_argument("--version", default="v0-wio")
    parser.add_argument("--node-id", default="demo-node")
    parser.add_argument("--node-secret", default="demo-secret")
    parser.add_argument("--checkpoint", default="runtime_data/wio_demo/checkpoint.json")
    parser.add_argument("--loose", action="store_true")
    args = parser.parse_args()

    task = call("POST", args.server, "/wio/task", {
        "plan": {"plan_id": "plan_wio_demo", "max_steps": 1, "estimated_total_tokens": 128},
        "node_id": args.node_id,
        "input_uri": "file://runtime_data/wio_demo/input.jsonl",
        "output_uri": "file://runtime_data/wio_demo/output/",
    })["item"]["task"]

    call("POST", args.server, f"/wio/tasks/{task['task_id']}/claim?node_id={args.node_id}")

    checkpoint_path = Path(args.checkpoint)
    write_checkpoint(checkpoint_path, args.name, args.version)
    receipt = signed_result({
        "task_id": task["task_id"],
        "checkpoint_uri": checkpoint_path.resolve().as_uri(),
        "checkpoint_hash": file_sha256(checkpoint_path),
        "token_count": 128,
        "train_loss": 0.1,
        "eval_loss": 0.1,
    }, node_id=args.node_id, secret=args.node_secret)

    submitted = call("POST", args.server, "/wio/result", {"payload": receipt, "require_valid": not args.loose})
    cataloged = call("POST", args.server, "/catalog/from-receipt", {
        "receipt": receipt,
        "name": args.name,
        "version": args.version,
        "kind": "checkpoint",
        "metrics": {"score": 0.8, "wio_demo": True},
        "require_valid": not args.loose,
    })
    item_id = cataloged["item"]["id"]
    validated = call("POST", args.server, f"/catalog/items/{item_id}/validate", {})
    notarized = call("POST", args.server, f"/catalog/items/{item_id}/notarize", {})
    published = call("POST", args.server, f"/catalog/items/{item_id}/publish", {})

    print(json.dumps({"ok": True, "task": task, "submitted": submitted, "cataloged": cataloged, "validated": validated, "notarized": notarized, "published": published}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
