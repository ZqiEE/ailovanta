from __future__ import annotations

import argparse
import json

from api.preflight import check


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local loop prerequisites")
    parser.add_argument("--core-path", default="../ailovanta-core")
    args = parser.parse_args()
    result = check(core_path=args.core_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
