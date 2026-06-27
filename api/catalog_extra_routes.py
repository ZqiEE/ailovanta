from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.catalog import Catalog
from api.model_job import merge_outputs


router = APIRouter()
catalog = Catalog()


class CombineIn(BaseModel):
    item_ids: list[str]
    name: str = "ailovanta-code"
    version: str = "merged-v0"
    output_dir: str | None = None


@router.post("/catalog/items/{item_id}/score")
def score_item(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    loc = Path(item["location"])
    exists = loc.exists()
    score = float((item.get("metrics") or {}).get("score", 0.0))
    passed = bool(exists and score >= 0.5)
    if passed:
        item = catalog.set_status(item_id, "validated") or item
    return {"item": item, "score": score, "passed": passed, "exists": exists}


@router.post("/catalog/combine")
def combine_items(body: CombineIn) -> dict:
    items = []
    for item_id in body.item_ids:
        item = catalog.get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"item not found: {item_id}")
        items.append(item)
    result = merge_outputs(items, body.output_dir or f"runtime_data/models/{body.name}-{body.version}")
    item = catalog.add({"name": body.name, "version": body.version, "source_job_id": "combine", "location": result["location"], "kind": "merged", "metrics": result["metrics"], "status": "candidate", "notes": result["summary"]})
    return {"item": item, "result": result}
