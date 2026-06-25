from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.node_proof import attach_proof, verify_proof

router = APIRouter(prefix="/node-proof", tags=["node-proof"])


class ProofRequest(BaseModel):
    payload: dict[str, Any]
    node_id: str
    secret: str


@router.post("/attach")
def attach(body: ProofRequest) -> dict[str, Any]:
    return {"ok": True, "payload": attach_proof(body.payload, body.node_id, body.secret)}


@router.post("/verify")
def verify(body: ProofRequest) -> dict[str, Any]:
    return verify_proof(body.payload, {body.node_id: body.secret})
