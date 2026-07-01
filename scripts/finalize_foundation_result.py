from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.foundation_result_finalize import finalize_foundation_result_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize foundation result artifact metadata from local backend ref")
    parser.add_argument("result_path")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    finalized = finalize_foundation_result_file(args.result_path, write=not args.check_only)
    print(json.dumps({"ok": True, "result_path": args.result_path, "written": not args.check_only, "artifact": finalized.get("artifact")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
