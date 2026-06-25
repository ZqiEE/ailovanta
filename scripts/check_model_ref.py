from __future__ import annotations

import argparse
import json

from api.route_gate import apply_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local model reference before owned runtime use")
    parser.add_argument("--model-id", default="ailovanta-owned")
    parser.add_argument("--version", default="candidate")
    args = parser.parse_args()
    report = apply_gate(args.model_id, args.version, "local-check")
    ok = report is None
    print(json.dumps({"ok": ok, "model_id": args.model_id, "version": args.version, "report": report}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
