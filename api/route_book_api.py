from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.route_book import RouteBook

router = APIRouter(prefix="/route-book", tags=["route-book"])
store = RouteBook()


class SetRouteBody(BaseModel):
    route_key: str
    model_key: str
    binding_id: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = {}


class DisableBody(BaseModel):
    reason: str | None = None


@router.post("/active")
def set_active(body: SetRouteBody) -> dict[str, Any]:
    return {"route": store.set_active(body.route_key, body.model_key, binding_id=body.binding_id, reason=body.reason, metadata=body.metadata)}


@router.get("")
def list_routes(limit: int = 100) -> dict[str, Any]:
    return {"items": store.list_routes(limit=limit)}


@router.get("/{route_key:path}")
def get_route(route_key: str) -> dict[str, Any]:
    item = store.get(route_key)
    if not item:
        raise HTTPException(status_code=404, detail="route not found")
    return {"route": item}


@router.post("/{route_key:path}/disable")
def disable(route_key: str, body: DisableBody) -> dict[str, Any]:
    item = store.disable(route_key, reason=body.reason)
    if not item:
        raise HTTPException(status_code=404, detail="route not found")
    return {"route": item}
