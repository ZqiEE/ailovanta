from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.model_job import run_model_job


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--payload", required=True)
    p.add_argument("--source-id", default="manual")
    p.add_argument("--gpu", action="store_true")
    args = p.parse_args()
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    profile = {"cpu_threads": 1, "memory_gb": 4.0, "has_gpu": args.gpu, "gpu_name": None}
    result = run_model_job(payload, profile, args.source_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
