from __future__ import annotations

from fastapi import APIRouter

from api.runtime_readiness import RuntimeReadiness


router = APIRouter()
checker = RuntimeReadiness()


@router.get("/ops/readiness/runtime-route")
def runtime_route_readiness(route_key: str = "owned-chat/default") -> dict:
    return checker.check_route(route_key)
