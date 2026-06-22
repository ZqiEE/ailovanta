from __future__ import annotations

from node_client.job_runner import JobRunner
from node_client.task_policy import TaskPolicy


def test_runner_returns_ok_for_allowed_job() -> None:
    runner = JobRunner(TaskPolicy.default())
    result = runner.run({"id": "job_ok", "type": "verification", "payload": {"samples": 1}})
    assert result.status == "ok"
    assert result.job_id == "job_ok"
    assert result.policy_reason == "accepted"


def test_runner_returns_failed_for_blocked_job() -> None:
    runner = JobRunner(TaskPolicy.default())
    result = runner.run({"id": "job_blocked", "type": "unknown_job", "payload": {}})
    assert result.status == "failed"
    assert result.job_id == "job_blocked"
    assert "not allowed" in result.policy_reason
