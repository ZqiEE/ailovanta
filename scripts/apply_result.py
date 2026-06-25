from __future__ import annotations

import argparse
import json

from api.receipt_apply import apply_result


def main() -> int:
    p = argparse.ArgumentParser(description="Apply a foundation result")
    p.add_argument("result")
    p.add_argument("--runtime-id", default="rt-owned-1")
    p.add_argument("--node-id", default="node-owned-1")
    args = p.parse_args()
    out = apply_result(args.result, runtime_id=args.runtime_id, node_id=args.node_id)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
