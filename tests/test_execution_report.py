from __future__ import annotations

from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner


def test_execution_report_contains_worker_fields() -> None:
    runner = JobRunner()
    job = {"id": "report_job", "type": "verification", "payload": {"samples": 1}}
    result = runner.run(job)
    report = build_execution_report("node_report", job, result)
    assert report["node_id"] == "node_report"
    assert report["job_id"] == "report_job"
    assert report["status"] == "ok"
    assert "policy_reason" in report
    assert "descriptor_reason" in report
