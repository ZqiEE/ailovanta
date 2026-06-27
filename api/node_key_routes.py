from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from api.node_security import NodeTokenStore
from api.node_token_lifecycle import revoke_node_token, rotate_node_token


router = APIRouter()
store = NodeTokenStore()


class IssueNodeTokenIn(BaseModel):
    node_id: str


def admin_guard(value: str | None) -> None:
    expected = os.environ.get("AILOVANTA_ADMIN_TOKEN", "")
    if expected and value != expected:
        raise HTTPException(status_code=401, detail="admin token required")


@router.post("/node-keys/issue")
def issue_node_key(body: IssueNodeTokenIn, x_ailovanta_admin_token: str | None = Header(default=None)) -> dict:
    admin_guard(x_ailovanta_admin_token)
    return store.issue(body.node_id)


@router.post("/node-keys/{node_id}/rotate")
def rotate_node_key(node_id: str, x_ailovanta_admin_token: str | None = Header(default=None)) -> dict:
    admin_guard(x_ailovanta_admin_token)
    return rotate_node_token(node_id)


@router.post("/node-keys/{node_id}/revoke")
def revoke_node_key(node_id: str, x_ailovanta_admin_token: str | None = Header(default=None)) -> dict:
    admin_guard(x_ailovanta_admin_token)
    return revoke_node_token(node_id)


@router.get("/node-keys")
def list_node_keys(x_ailovanta_admin_token: str | None = Header(default=None)) -> dict:
    admin_guard(x_ailovanta_admin_token)
    data = store.all()
    return {"nodes": sorted(data.keys()), "count": len(data)}
