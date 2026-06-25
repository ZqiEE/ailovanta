from __future__ import annotations

import argparse
import json

from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def main() -> int:
    parser = argparse.ArgumentParser(description="Import distributed foundation result and prepare runtime")
    parser.add_argument("result")
    parser.add_argument("--model-key", default=None)
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    parser.add_argument("--no-prepare", action="store_true")
    args = parser.parse_args()
    imported = import_foundation_result_file(args.result)
    artifact = (imported.get("artifact_binding") or {})
    model_key = args.model_key or artifact.get("model_key") or "ailovanta-owned:candidate"
    before = OwnedDoctor().check(model_key)
    prepare = None
    if not args.no_prepare:
        prepare = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=args.runtime_id, node_id=args.node_id))
    after = OwnedDoctor().check(model_key)
    print(json.dumps({"ok": after.get("ok"), "imported": imported, "doctor_before": before, "prepare": prepare, "doctor_after": after}, ensure_ascii=False, indent=2))
    return 0 if after.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
