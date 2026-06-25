from __future__ import annotations

import argparse
import json

from api.g2 import run_gate


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("result")
    p.add_argument("--core", default="../ailovanta-core")
    p.add_argument("--work", default="runtime_data/g2")
    a = p.parse_args()
    data = run_gate(a.result, core_path=a.core, work_dir=a.work)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    decision = ((data.get("gate") or {}).get("decision") or {}).get("decision")
    return 0 if decision in {"promote", "shadow"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
