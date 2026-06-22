from __future__ import annotations

import argparse
import json
from pathlib import Path

from node_client.report_store import ReportStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Export local worker reports")
    parser.add_argument("--db", default="runtime_data/worker_reports.sqlite3")
    parser.add_argument("--output", default="runtime_data/worker_reports_export.json")
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    store = ReportStore(args.db)
    data = {
        "summary": store.summary(),
        "reports": store.list_reports(node_id=args.node_id, status=args.status, limit=args.limit),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
