from __future__ import annotations

import argparse
import json

from api.node_trust import NodeTrustStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage node trust registry")
    parser.add_argument("action", choices=["register", "disable", "enable", "list", "get"])
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--secret", default=None)
    parser.add_argument("--trust-score", type=float, default=0.8)
    args = parser.parse_args()
    store = NodeTrustStore()
    if args.action == "register":
        if not args.node_id or not args.secret:
            raise SystemExit("--node-id and --secret required")
        out = store.register(args.node_id, args.secret, trust_score=args.trust_score)
    elif args.action == "disable":
        if not args.node_id:
            raise SystemExit("--node-id required")
        out = store.set_status(args.node_id, "disabled")
    elif args.action == "enable":
        if not args.node_id:
            raise SystemExit("--node-id required")
        out = store.set_status(args.node_id, "active")
    elif args.action == "get":
        if not args.node_id:
            raise SystemExit("--node-id required")
        out = store.get(args.node_id)
    else:
        out = {"items": store.list_nodes()}
    print(json.dumps({"ok": out is not None, "result": out}, ensure_ascii=False, indent=2))
    return 0 if out is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
