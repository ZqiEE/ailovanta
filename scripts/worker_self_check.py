from __future__ import annotations

from dataclasses import asdict

from node_client.job_runner import JobRunner
from node_client.task_policy import TaskPolicy


def main() -> None:
    runner = JobRunner(TaskPolicy.default())
    jobs = [
        {"id": "selfcheck_eval", "type": "evaluation", "payload": {"samples": 1}},
        {"id": "selfcheck_verify", "type": "verification", "payload": {"samples": 1}},
        {"id": "selfcheck_blocked", "type": "unknown_job", "payload": {}},
    ]
    for job in jobs:
        print(asdict(runner.run(job)))


if __name__ == "__main__":
    main()
