from __future__ import annotations

import argparse
import json
import os
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit a signed receipt for a local checkpoint/adapter file")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--node-secret", default=os.environ.get("AILOVANTA_WORKER_SECRET", ""))
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--token-count", type=int, default=0)
    parser.add_argument("--train-loss", type=float, default=0.0)
    parser.add_argument("--eval-loss", type=float, default=0.0)
    parser.add_argument("--loose", action="store_true")
    args = parser.parse_args()
    if not args.node_secret:
        raise SystemExit("--node-secret or AILOVANTA_WORKER_SECRET is required")
    path = Path(args.checkpoint)
    if not path.exists():
        raise FileNotFoundError(str(path))
    receipt = signed_result({
        "task_id": args.task_id,
        "checkpoint_uri": path.resolve().as_uri(),
        "checkpoint_hash": file_sha256(path),
        "token_count": args.token_count,
        "train_loss": args.train_loss,
        "eval_loss": args.eval_loss,
    }, node_id=args.node_id, secret=args.node_secret)
    result = call("POST", args.server, "/wio/result", {"payload": receipt, "require_valid": not args.loose})
    print(json.dumps({"ok": True, "receipt": receipt, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
