from __future__ import annotations

import json
from typing import Any

from api.ollama_adapter import OllamaAdapter, OllamaConfig, OllamaUnavailable


ALLOWED_NETWORK_PRIVACY_SCOPES = {"public", "synthetic"}


def run_coding_inference(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    privacy_scope = str(payload.get("privacy_scope") or "").strip().lower()
    if privacy_scope not in ALLOWED_NETWORK_PRIVACY_SCOPES:
        raise RuntimeError("community inference refuses private or unlabeled payloads")

    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise RuntimeError("coding inference prompt is empty")
    if len(prompt.encode("utf-8")) > 196_608:
        raise RuntimeError("coding inference prompt is too large")

    model_name = str(payload.get("model") or "qwen2.5-coder:7b")
    context_length = max(2048, min(int(payload.get("context_length") or 16384), 131072))
    model = OllamaAdapter(
        OllamaConfig(
            base_url="http://127.0.0.1:11434",
            model=model_name,
            timeout_seconds=300.0,
            context_length=context_length,
        )
    )
    try:
        answer = model.chat_messages([{"role": "user", "content": prompt}], mode="coding", memory=[])
    except OllamaUnavailable as exc:
        raise RuntimeError("local Ollama inference failed: " + str(exc)) from exc

    return {
        "schema_version": "ailovanta.public_coding_inference.v1",
        "job_id": str(job.get("id") or job.get("job_id") or "unknown"),
        "privacy_scope": privacy_scope,
        "model": model_name,
        "answer": answer,
    }


def summary_json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True)
