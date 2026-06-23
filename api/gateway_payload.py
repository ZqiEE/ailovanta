from __future__ import annotations

from api.content_addressing import hash_object


def build_gateway_payload(prompt: str, user_ref: str = "anonymous", tag: str | None = None, min_score: float = 0.0, require_gpu: bool = False) -> dict:
    prompt_hash = hash_object({"prompt": prompt})
    request_id = "req_" + hash_object({"user_ref": user_ref, "prompt_hash": prompt_hash, "tag": tag})[:16]
    return {
        "request_id": request_id,
        "user_ref": user_ref,
        "prompt_hash": prompt_hash,
        "prompt": prompt,
        "tag": tag,
        "min_score": min_score,
        "require_gpu": require_gpu,
    }
