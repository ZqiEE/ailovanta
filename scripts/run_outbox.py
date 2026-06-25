from __future__ import annotations

import argparse
import json

from api.outbox_run import run_from_payload
from api.parcel_store import ParcelStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Run receipt flow from the latest outbox item")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--result-output", default="runtime_data/parcels/foundation_result.json")
    args = parser.parse_args()
    items = ParcelStore().list_outbox()
    if not items:
        print(json.dumps({"ok": False, "reason": "empty outbox"}, ensure_ascii=False, indent=2))
        return 1
    payload = {**items[-1], "apply_flow": True, "plan_path": args.plan, "core_path": args.core_path, "result_output": args.result_output}
    result = run_from_payload(payload)
    print(json.dumps({"ok": bool(result and result.get("ok")), "run": result}, ensure_ascii=False, indent=2))
    return 0 if result and result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
