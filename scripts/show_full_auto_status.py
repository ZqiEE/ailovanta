from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.artifact_binding import ArtifactBindingStore
from api.gpu_probe import detect_gpu
from api.github_source_frontier import load_frontier
from api.replica_book import status as replica_status
from api.replica_repair import ReplicaRepairStore
from api.storage import SchedulerStore


def main() -> int:
    state_path = ROOT / "runtime_data" / "full_auto_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8-sig")) if state_path.exists() else {}
    scheduler = SchedulerStore(ROOT / "runtime_data" / "scheduler.sqlite3")
    bindings = ArtifactBindingStore(ROOT / "runtime_data" / "artifact_bindings.sqlite3")
    repair_store = ReplicaRepairStore(path=ROOT / "runtime_data" / "replica_repair_tasks.json", replica_book_path=ROOT / "runtime_data" / "replica_book.json")
    latest_binding = bindings.latest_for_model("ailovanta-owned:candidate", active_only=True)
    repair_tasks = repair_store.list_tasks(limit=20)
    source_frontier = load_frontier(ROOT / "runtime_data" / "github_source_frontier.json")
    source_queries = sorted(
        source_frontier.get("queries", {}).values(),
        key=lambda item: (float(item.get("priority") or 0), float(item.get("last_run_at") or 0)),
        reverse=True,
    )[:10]
    payload = {
        "ok": True,
        "state": state,
        "gpu": detect_gpu(),
        "scheduler": scheduler.status(),
        "latest_owned_binding": latest_binding,
        "replica_status": replica_status(ROOT / "runtime_data" / "replica_book.json"),
        "replica_repairs": {
            "queued": len([task for task in repair_tasks if task.get("status") == "queued"]),
            "assigned": len([task for task in repair_tasks if task.get("status") == "assigned"]),
            "done": len([task for task in repair_tasks if task.get("status") == "done"]),
            "tasks": repair_tasks,
        },
        "source_frontier": {
            "schema_version": source_frontier.get("schema_version"),
            "query_count": len(source_frontier.get("queries", {})),
            "top_queries": source_queries,
        },
        "jobs": scheduler.list_jobs(limit=10),
        "nodes": scheduler.list_nodes(limit=10),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
