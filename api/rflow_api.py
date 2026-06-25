from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.receipt_flow import build_and_apply, build_result

router = APIRouter(prefix="/rflow", tags=["rflow"])


class FlowRequest(BaseModel):
    plan_path: str
    core_path: str = "../ailovanta-core"
    result_output: str = "runtime_data/parcels/foundation_result.json"
    apply_public: bool = True


@router.post("/run")
def run_flow(body: FlowRequest) -> dict[str, Any]:
    if body.apply_public:
        return build_and_apply(plan_path=body.plan_path, core_path=body.core_path, result_output=body.result_output)
    return build_result(plan_path=body.plan_path, core_path=body.core_path, result_output=body.result_output)
