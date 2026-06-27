from __future__ import annotations

import hmac
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api.local_runtime import LocalRuntime


app = FastAPI(title="Ailovanta Runtime Node", version="0.1.0")
runtime = LocalRuntime()


def guard(value: str | None) -> None:
    expected = os.environ.get("AILOVANTA_RUNTIME_KEY", "")
    if expected and not hmac.compare_digest(value or "", expected):
        raise HTTPException(status_code=401, detail="runtime key required")


class LoadRequest(BaseModel):
    model_key: str
    location: str


class GenerateRequest(BaseModel):
    model_key: str
    prompt: str
    max_new_tokens: int = Field(default=128, ge=1, le=2048)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "loaded": runtime.list()}


@app.post("/load")
def load_model(body: LoadRequest, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    guard(x_ailovanta_node_token)
    return runtime.load(body.model_key, body.location)


@app.get("/models")
def list_models() -> dict:
    return {"models": runtime.list()}


@app.post("/generate")
def generate(body: GenerateRequest, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    guard(x_ailovanta_node_token)
    return runtime.generate(body.model_key, body.prompt, body.max_new_tokens)
