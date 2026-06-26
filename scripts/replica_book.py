from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.replica_book import add_manifest, status


def newest_manifest(root: str | Path = "runtime_data/manifests") -> Path | None:
    folder = Path(root)
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> int:
    p = argparse.ArgumentParser(description="Register artifact manifest copies")
    p.add_argument("--manifest")
    p.add_argument("--node-id", default="local-storage")
    p.add_argument("--status", action="store_true")
    args = p.parse_args()
    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    path = Path(args.manifest) if args.manifest else newest_manifest()
    if not path or not path.exists():
        print(json.dumps({"ok": False, "error": "no manifest found"}, ensure_ascii=False, indent=2))
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8"))
    book = add_manifest(manifest, node_id=args.node_id)
    print(json.dumps({"ok": True, "book": book, "status": status()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
