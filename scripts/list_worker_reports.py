from __future__ import annotations

import argparse
import json

from node_client.report_store import ReportStore


def main() -> None:
    parser = argparse.ArgumentParser(description="List local worker reports")
    parser.add_argument("--db", default="runtime_data/worker_reports.sqlite3")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    store = ReportStore(args.db)
    data = {"summary": store.summary(), "reports": store.list_reports(limit=args.limit)}
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
