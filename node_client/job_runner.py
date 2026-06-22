from __future__ import annotations

import time
from dataclasses import dataclass

from node_client.task_policy import TaskPolicy


@dataclass
class JobRunResult:
    job_id: str
    status: str
    output_summary: str
    runtime_seconds: float
    policy_reason: str = "accepted"


class JobRunner:
    """Safe simulated runner for local MVP nodes.

    It does not execute arbitrary code. It validates task type and payload size,
    then returns a simulated execution report.
    """

    def __init__(self, policy: TaskPolicy | None = None) -> None:
        self.policy = policy or TaskPolicy.default()

    def run(self, job: dict) -> JobRunResult:
        start = time.time()
        job_type = job.get("type", "unknown")
        ok, reason = self.policy.validate(job)
        if not ok:
            return JobRunResult(
                job_id=job.get("id", "unknown"),
                status="failed",
                output_summary=f"rejected by worker policy: {reason}",
                runtime_seconds=round(time.time() - start, 3),
                policy_reason=reason,
            )

        simulated_seconds = min(self._simulated_seconds(job_type), self.policy.max_runtime_seconds)
        time.sleep(simulated_seconds)
        runtime = round(time.time() - start, 3)
        if runtime > self.policy.max_runtime_seconds:
            return JobRunResult(
                job_id=job["id"],
                status="failed",
                output_summary="worker timeout",
                runtime_seconds=runtime,
                policy_reason="timeout",
            )
        return JobRunResult(
            job_id=job["id"],
            status="ok",
            output_summary=f"simulated safe result for {job_type}",
            runtime_seconds=runtime,
            policy_reason=reason,
        )

    @staticmethod
    def _simulated_seconds(job_type: str) -> float:
        return {
            "rag_index": 0.5,
            "rag_import": 0.6,
            "evaluation": 0.7,
            "evaluation_batch": 0.8,
            "verification": 0.4,
            "lora_micro": 1.0,
        }.get(job_type, 0.6)
