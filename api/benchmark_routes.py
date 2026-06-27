from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.benchmark_suite import load_cases, score_catalog_item, score_text
from api.catalog import Catalog


router = APIRouter()
catalog = Catalog()


class TextBenchmarkIn(BaseModel):
    text: str
    case_path: str | None = None


@router.get("/benchmarks/cases")
def benchmark_cases() -> dict:
    return {"cases": load_cases()}


@router.post("/benchmarks/text")
def benchmark_text(body: TextBenchmarkIn) -> dict:
    return score_text(body.text, load_cases(body.case_path))


@router.post("/benchmarks/catalog/{item_id}")
def benchmark_catalog_item(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    result = score_catalog_item(item)
    if result["passed"]:
        item = catalog.set_status(item_id, "validated") or item
    return {"item": item, "benchmark": result}
