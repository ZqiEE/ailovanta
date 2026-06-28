from __future__ import annotations

from fastapi import APIRouter

from api.result_guard_check import check_result_guard


router = APIRouter(prefix="/ops/result-guard", tags=["result-guard"])


@router.get("/ready")
def result_guard_ready() -> dict:
    return check_result_guard()
