from __future__ import annotations

from typing import Any

from api.node_proof import attach_proof, verify_proof
from api.wc import make_result, make_task


def task_envelope(plan: dict[str, Any], node_id: str, input_uri: str, output_uri: str) -> dict[str, Any]:
    return {"kind": "worker_task", "task": make_task(plan, node_id, input_uri, output_uri)}


def signed_result(payload: dict[str, Any], node_id: str, secret: str) -> dict[str, Any]:
    result = make_result({**payload, "node_id": node_id})
    return attach_proof(result, node_id=node_id, secret=secret)


def verify_result(payload: dict[str, Any]) -> dict[str, Any]:
    proof = verify_proof(payload)
    return {"ok": bool(proof.get("valid")), "proof": proof, "result": payload}
