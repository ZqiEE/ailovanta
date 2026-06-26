from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_eval import eval_repo, save_eval


def main() -> int:
    p = argparse.ArgumentParser(description="Run code checks")
    p.add_argument("--source", default=".")
    p.add_argument("--output", default="runtime_data/code_eval.json")
    args = p.parse_args()
    result = save_eval(eval_repo(args.source), args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if int(result.get("failed", 0) or 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
