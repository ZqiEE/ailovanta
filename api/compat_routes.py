from __future__ import annotations

from fastapi import APIRouter

from api.compat_check import check_local_stack


router = APIRouter()


@router.get("/compat/local")
def local_compatibility() -> dict:
    return check_local_stack()
