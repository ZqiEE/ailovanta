from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.model_backend_client import ModelBackendClient

app = FastAPI(title="Ailovanta Worker", version="1.0.0")

client = ModelBackendClient()

class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    try:
        answer = client.chat(prompt=body.prompt)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "answer": answer,
        "source": "ailovanta-worker-v1",
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
    }