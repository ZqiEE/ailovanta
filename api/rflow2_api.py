from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.receipt_flow_v2 import build_and_apply_v2, build_result_v2

router = APIRouter(prefix="/rflow2", tags=["rflow2"])


class Flow2Request(BaseModel):
    plan_path: str
    core_path: str = "../ailovanta-core"
    result_output: str = "runtime_data/parcels/foundation_result.json"
    apply_public: bool = True


@router.post("/run")
def run_flow2(body: Flow2Request) -> dict[str, Any]:
    if body.apply_public:
        return build_and_apply_v2(plan_path=body.plan_path, core_path=body.core_path, result_output=body.result_output)
    return build_result_v2(plan_path=body.plan_path, core_path=body.core_path, result_output=body.result_output)
