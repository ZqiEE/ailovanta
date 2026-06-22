from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time

from api.content_addressing import hash_object


@dataclass
class TaskProof:
    proof_id: str
    node_id: str
    job_id: str
    job_type: str
    report_hash: str
    result_status: str
    runtime_seconds: float
    created_at: float


def build_task_proof(report: dict) -> dict:
    report_hash = hash_object(report)
    proof_payload = {
        "node_id": report["node_id"],
        "job_id": report["job_id"],
        "job_type": report["job_type"],
        "report_hash": report_hash,
    }
    proof = TaskProof(
        proof_id="proof_" + hash_object(proof_payload)[:16],
        node_id=report["node_id"],
        job_id=report["job_id"],
        job_type=report["job_type"],
        report_hash=report_hash,
        result_status=report["status"],
        runtime_seconds=float(report.get("runtime_seconds", 0)),
        created_at=round(time(), 3),
    )
    return asdict(proof)
