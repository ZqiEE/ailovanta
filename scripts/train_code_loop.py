from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_data import build_records, write_jsonl


def main() -> int:
    p = argparse.ArgumentParser(description="Build code corpus and run local shard training")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--source", default=".", help="Local repo or folder to use as code data")
    p.add_argument("--output", default="runtime_data/code_corpus.jsonl")
    p.add_argument("--model-id", default="ailovanta-code")
    p.add_argument("--version", default="v0.1-code")
    p.add_argument("--total-tokens", type=int, default=4096)
    p.add_argument("--shard-tokens", type=int, default=512)
    p.add_argument("--node-runs", type=int, default=8)
    args = p.parse_args()

    records = build_records(args.source)
    corpus = write_jsonl(records, args.output)
    print(json.dumps({"code_corpus": corpus}, ensure_ascii=False, indent=2))
    if corpus["records"] == 0:
        raise SystemExit("no code records found")

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/full_local_loop.py",
            "--api-url",
            args.api_url,
            "--data-file",
            args.output,
            "--total-tokens",
            str(args.total_tokens),
            "--shard-tokens",
            str(args.shard_tokens),
            "--node-runs",
            str(args.node_runs),
            "--model-id",
            args.model_id,
            "--version",
            args.version,
        ],
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
