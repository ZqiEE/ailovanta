from __future__ import annotations

import os
import sys

import httpx


def main() -> int:
    api_url = os.getenv("AILOVANTA_API_URL", "http://127.0.0.1:8000").rstrip("/")
    prompt = os.getenv("AILOVANTA_TEST_PROMPT", "Say hello from Ailovanta owned runtime.")
    payload = {
        "prompt": prompt,
        "user_id": "local",
        "title": "Owned runtime smoke test",
        "model_id": os.getenv("AILOVANTA_OWNED_MODEL_ID", "ailovanta-owned"),
        "version": os.getenv("AILOVANTA_OWNED_MODEL_VERSION", "candidate"),
        "policy_mode": "open_research",
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(api_url + "/ailovanta/v1/owned-chat", json=payload)
        response.raise_for_status()
        data = response.json()
    print(data)
    if not data.get("owned_model_ready"):
        raise RuntimeError("owned model is not ready")
    if data.get("source") not in {"ailovanta-worker", "ailovanta-worker-v1", "ailovanta-worker-local-runtime", "ailovanta-worker-backend"}:
        raise RuntimeError("unexpected owned chat source: " + str(data.get("source")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("owned chat smoke call failed", exc, file=sys.stderr)
        raise SystemExit(1)
