from __future__ import annotations

import argparse
import json

from api.chunk_manifest import build_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build artifact chunk manifest")
    parser.add_argument("path")
    parser.add_argument("--chunk-size", type=int, default=8 * 1024 * 1024)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--min-replicas", type=int, default=3)
    args = parser.parse_args()
    data = build_manifest(args.path, chunk_size=args.chunk_size, sources=args.source or None, min_replicas=args.min_replicas)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
