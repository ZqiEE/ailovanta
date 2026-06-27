from __future__ import annotations


def ready_for_catalog_publish(item: dict) -> dict:
    artifact_hash = item.get("artifact_hash") or item.get("digest")
    if not artifact_hash:
        return {"ok": False, "reason": "artifact hash required"}
    if not str(artifact_hash).startswith("sha256:"):
        return {"ok": False, "reason": "artifact hash must be sha256"}
    proof = item.get("proof")
    if not isinstance(proof, dict):
        return {"ok": False, "reason": "worker receipt required"}
    if not proof.get("ok"):
        return {"ok": False, "reason": "worker receipt must be valid", "proof": proof}
    result = proof.get("result") if isinstance(proof.get("result"), dict) else {}
    result_hash = result.get("checkpoint_hash")
    if result_hash and result_hash != artifact_hash:
        return {"ok": False, "reason": "artifact hash does not match worker receipt", "artifact_hash": artifact_hash, "receipt_hash": result_hash}
    anchor = item.get("anchor_receipt")
    if not isinstance(anchor, dict):
        return {"ok": False, "reason": "anchor receipt required"}
    anchor_hash = anchor.get("payload_hash")
    if anchor_hash and anchor_hash not in {artifact_hash, result_hash}:
        return {"ok": False, "reason": "anchor receipt does not reference artifact hash", "anchor_hash": anchor_hash, "artifact_hash": artifact_hash}
    return {"ok": True, "artifact_hash": artifact_hash}
