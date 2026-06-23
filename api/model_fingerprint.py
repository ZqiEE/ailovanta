from __future__ import annotations

from api.content_addressing import hash_object


def build_output_fingerprint(package_hash: str, node_id: str, task_id: str, output_text: str) -> dict:
    public_payload = {
        "package_hash": package_hash,
        "node_id": node_id,
        "task_id": task_id,
        "output_hash": hash_object({"text": output_text}),
    }
    return {
        "fingerprint_id": "fp_" + hash_object(public_payload)[:16],
        "package_hash": package_hash,
        "node_id": node_id,
        "task_id": task_id,
        "output_hash": public_payload["output_hash"],
    }


def verify_output_fingerprint(fingerprint: dict, output_text: str) -> bool:
    return fingerprint.get("output_hash") == hash_object({"text": output_text})
