from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    data = json.loads(Path("docs/commercial_checklist.json").read_text(encoding="utf-8"))
    done = set(data.get("local_scaffold_done", []))
    required = set(data.get("required_before_commercial_use", []))
    external = set(data.get("external_resources_needed", []))
    missing = sorted((required | external) - done)
    result = {"ok": not missing, "missing": missing, "local_scaffold_done": sorted(done)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
