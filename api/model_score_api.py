from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.model_score_store import ModelScoreStore

router = APIRouter(prefix="/model-scores", tags=["model-scores"])
store = ModelScoreStore()


class RecordScoreRequest(BaseModel):
    model_key: str
    score: float
    source: str = "manual"
    metrics: dict[str, Any] = {}


class AcceptRequest(BaseModel):
    model_key: str
    candidate_score: float
    min_delta: float = 0.0


@router.post("/record")
def record_score(body: RecordScoreRequest) -> dict[str, Any]:
    return {"ok": True, "score": store.record(body.model_key, body.score, body.source, body.metrics)}


@router.post("/accept")
def should_accept(body: AcceptRequest) -> dict[str, Any]:
    return {"ok": True, "decision": store.should_accept(body.model_key, body.candidate_score, body.min_delta)}


@router.get("/{model_key:path}/best")
def best_score(model_key: str) -> dict[str, Any]:
    return {"ok": True, "best": store.best(model_key)}


@router.get("/{model_key:path}/history")
def score_history(model_key: str, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "items": store.history(model_key, limit=limit)}
