from __future__ import annotations

import argparse
import json
import subprocess
import sys


def call(cmd: list[str]) -> dict:
    print("RUN", " ".join(cmd))
    code = subprocess.run(cmd, check=False).returncode
    return {"cmd": cmd, "returncode": code}


def main() -> int:
    p = argparse.ArgumentParser(description="Run compact code model pipeline")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--sources", default="runtime_data/github_code_sources.json")
    p.add_argument("--eval-source", default=".")
    p.add_argument("--total-tokens", type=int, default=8192)
    p.add_argument("--shard-tokens", type=int, default=512)
    p.add_argument("--node-runs", type=int, default=8)
    p.add_argument("--min-score", type=float, default=1.0)
    steps = []
    args = p.parse_args()
    cmds = [
        [sys.executable, "scripts/train_github_code_loop.py", "--api-url", args.api_url, "--sources", args.sources, "--total-tokens", str(args.total_tokens), "--shard-tokens", str(args.shard_tokens), "--node-runs", str(args.node_runs)],
        [sys.executable, "scripts/check_code.py", "--source", args.eval_source],
        [sys.executable, "scripts/ckpt_manifest.py"],
        [sys.executable, "scripts/pool_store.py", "put"],
        [sys.executable, "scripts/replica_book.py"],
        [sys.executable, "scripts/promote_model.py", "--min-score", str(args.min_score)],
    ]
    for cmd in cmds:
        result = call(cmd)
        steps.append(result)
        if result["returncode"] != 0:
            print(json.dumps({"ok": False, "failed": result, "steps": steps}, ensure_ascii=False, indent=2))
            return int(result["returncode"])
    print(json.dumps({"ok": True, "steps": steps}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
