from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LEDGER_PATH = Path("runtime_data/credits.json")


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "ailovanta.credit_ledger.v1", "nodes": {}, "events": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(data: dict[str, Any], path: Path = LEDGER_PATH) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def award(node_id: str, amount: float, reason: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_ledger()
    nodes = data.setdefault("nodes", {})
    current = float(nodes.get(node_id, {}).get("credits", 0.0))
    nodes[node_id] = {"node_id": node_id, "credits": round(current + amount, 6)}
    data.setdefault("events", []).append({"node_id": node_id, "amount": amount, "reason": reason, "meta": meta or {}})
    return save_ledger(data)


def award_verified_items(items: list[dict[str, Any]], base_amount: float = 1.0) -> dict[str, Any]:
    data = load_ledger()
    seen = {event.get("meta", {}).get("result_id") for event in data.get("events", []) if event.get("reason") == "verified_delta"}
    for item in items:
        if not item.get("hash_ok"):
            continue
        result_id = item.get("result_id")
        if result_id in seen:
            continue
        token_count = float(item.get("token_count") or 1.0)
        amount = base_amount * max(token_count, 1.0)
        node_id = str(item.get("node_id") or "unknown")
        current = float(data.setdefault("nodes", {}).get(node_id, {}).get("credits", 0.0))
        data["nodes"][node_id] = {"node_id": node_id, "credits": round(current + amount, 6)}
        data.setdefault("events", []).append({"node_id": node_id, "amount": amount, "reason": "verified_delta", "meta": item})
    return save_ledger(data)
