from __future__ import annotations

from fastapi import APIRouter

from api.alert_summary import AlertSummary


router = APIRouter(prefix="/ops/alerts", tags=["alerts"])
summary = AlertSummary()


@router.get("/summary")
def alert_summary(route_key: str = "owned-chat/default", verify_bytes: bool = False) -> dict:
    return summary.collect(route_key=route_key, verify_bytes=verify_bytes)
