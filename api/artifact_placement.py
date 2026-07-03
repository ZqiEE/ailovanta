from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.runtime_store import RuntimeStore

PLACEMENT_SCHEMA = "ailovanta.artifact_placement.v1"


def lan_nodes(runtime_store: RuntimeStore | None = None) -> list[dict[str, Any]]:
    store = runtime_store or RuntimeStore()
    return [node for node in store.list_runtimes() if node.get("status") == "online"]


def plan_shard_placement(manifest: dict[str, Any], replication: int = 2, runtime_store: RuntimeStore | None = None) -> dict[str, Any]:
    nodes = lan_nodes(runtime_store)
    if not nodes:
        raise ValueError("no online runtime nodes available for placement")
    shards = list(manifest.get("shards") or [])
    if not shards:
        raise ValueError("manifest has no shards")
    replication = max(1, min(replication, len(nodes)))
    assignments = []
    for shard in shards:
        start = int(shard["index"]) % len(nodes)
        selected = [nodes[(start + offset) % len(nodes)] for offset in range(replication)]
        assignments.append(
            {
                "shard_index": shard["index"],
                "shard_hash": shard.get("hash"),
                "size_bytes": shard.get("size_bytes"),
                "nodes": [
                    {"runtime_id": node.get("runtime_id"), "node_id": node.get("node_id"), "region": node.get("region"), "pool": node.get("pool")}
                    for node in selected
                ],
            }
        )
    return {
        "schema_version": PLACEMENT_SCHEMA,
        "artifact_hash": manifest.get("artifact_hash"),
        "shard_count": len(shards),
        "replication": replication,
        "node_count": len(nodes),
        "assignments": assignments,
    }


def write_placement(plan: dict[str, Any], out_dir: str | Path = "runtime_data/artifact_placements") -> dict[str, Any]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    safe_hash = str(plan.get("artifact_hash") or "artifact").replace(":", "_")
    path = root / (safe_hash + ".placement.json")
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"placement_path": str(path), "placement": plan}


def verify_placement(plan: dict[str, Any]) -> dict[str, Any]:
    missing = []
    under_replicated = []
    expected = int(plan.get("replication") or 1)
    for item in plan.get("assignments", []):
        nodes = item.get("nodes") or []
        if not nodes:
            missing.append(item.get("shard_index"))
        if len(nodes) < expected:
            under_replicated.append(item.get("shard_index"))
    return {"ok": not missing and not under_replicated, "missing": missing, "under_replicated": under_replicated, "assignment_count": len(plan.get("assignments", []))}
