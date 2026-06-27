from __future__ import annotations

from typing import Any

from api.node_proof import attach_proof, verify_proof
from api.wc import make_result, make_task


def task_envelope(plan: dict[str, Any], node_id: str, input_uri: str, output_uri: str) -> dict[str, Any]:
    return {"kind": "worker_task", "task": make_task(plan, node_id, input_uri, output_uri)}


def signed_result(payload: dict[str, Any], node_id: str, secret: str) -> dict[str, Any]:
    result = make_result({**payload, "node_id": node_id})
    return attach_proof(result, node_id=node_id, secret=secret)


def result_shape(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ["task_id", "node_id", "checkpoint_uri", "checkpoint_hash", "node_proof"]:
        if not payload.get(key):
            return {"ok": False, "reason": f"missing_{key}"}
    if not str(payload.get("checkpoint_hash", "")).startswith("sha256:"):
        return {"ok": False, "reason": "bad_checkpoint_hash"}
    if not str(payload.get("checkpoint_uri", "")).startswith(("s3://", "ipfs://", "file://", "http://", "https://")):
        return {"ok": False, "reason": "bad_checkpoint_uri"}
    return {"ok": True}


def verify_result(payload: dict[str, Any]) -> dict[str, Any]:
    shape = result_shape(payload)
    if not shape.get("ok"):
        return {"ok": False, "shape": shape, "proof": None, "result": payload}
    proof = verify_proof(payload)
    return {"ok": bool(proof.get("ok") or proof.get("valid")), "shape": shape, "proof": proof, "result": payload}
