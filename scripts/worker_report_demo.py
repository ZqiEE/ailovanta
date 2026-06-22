from __future__ import annotations

import json

from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner


def main() -> None:
    runner = JobRunner()
    jobs = [
        {"id": "report_eval", "type": "evaluation", "payload": {"samples": 2}},
        {"id": "report_blocked", "type": "unknown_job", "payload": {}},
    ]
    for job in jobs:
        result = runner.run(job)
        report = build_execution_report("node_report_demo", job, result)
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
