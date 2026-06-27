from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.catalog import Catalog
from api.strong_benchmark import write_benchmark_report


router = APIRouter()
catalog = Catalog()


class PathBenchmarkIn(BaseModel):
    path: str
    output_path: str | None = None


@router.post("/benchmarks/path")
def benchmark_path(body: PathBenchmarkIn) -> dict:
    return write_benchmark_report(body.path, body.output_path)


@router.post("/benchmarks/catalog/{item_id}/strong")
def benchmark_catalog_strong(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    report_path = f"{item['location']}/benchmark_report.json"
    report = write_benchmark_report(item["location"], report_path)
    if report["passed"]:
        item = catalog.set_status(item_id, "validated") or item
    return {"item": item, "benchmark": report, "report_path": report_path}
