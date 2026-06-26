from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.pool_store import get, info, load_manifest, put


def newest_manifest(root: str | Path = "runtime_data/manifests") -> Path | None:
    folder = Path(root)
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> int:
    p = argparse.ArgumentParser(description="Local artifact pool store")
    sub = p.add_subparsers(dest="cmd", required=True)
    put_p = sub.add_parser("put")
    put_p.add_argument("--manifest")
    get_p = sub.add_parser("get")
    get_p.add_argument("--manifest")
    get_p.add_argument("--output", required=True)
    sub.add_parser("status")
    args = p.parse_args()
    if args.cmd == "status":
        print(json.dumps(info(), ensure_ascii=False, indent=2))
        return 0
    manifest_path = Path(args.manifest) if args.manifest else newest_manifest()
    if not manifest_path or not manifest_path.exists():
        print(json.dumps({"ok": False, "error": "manifest not found"}, ensure_ascii=False, indent=2))
        return 1
    manifest = load_manifest(manifest_path)
    if args.cmd == "put":
        print(json.dumps(put(manifest), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(get(manifest, args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
