from __future__ import annotations

import json

from api.coding_release_gate import coding_release_gate


def main() -> int:
    result = coding_release_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
