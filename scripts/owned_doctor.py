from __future__ import annotations

import argparse
import json

from api.owned_doctor import OwnedDoctor


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose owned runtime readiness")
    parser.add_argument("--model-key", default="ailovanta-owned:candidate")
    args = parser.parse_args()
    report = OwnedDoctor().check(args.model_key)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
