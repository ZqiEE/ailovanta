from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_data import build_records, write_jsonl


def main() -> int:
    p = argparse.ArgumentParser(description="Build a local code corpus for Ailovanta training")
    p.add_argument("--source", required=True, help="Local repo or folder to scan")
    p.add_argument("--output", default="runtime_data/code_corpus.jsonl")
    p.add_argument("--max-file-bytes", type=int, default=512_000)
    args = p.parse_args()
    records = build_records(args.source, max_file_bytes=args.max_file_bytes)
    result = write_jsonl(records, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
