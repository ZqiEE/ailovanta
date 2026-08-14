from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.coding_product_routes import build_coding_product_router
from api.coding_routes import build_coding_router
from api.network_routes import build_network_router
from api.storage import SchedulerStore


BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

# The public coding/control product is self-contained: local files + SQLite.
# In private-local mode Ollama also runs on this same computer. Community nodes
# connect to the lightweight network routes without importing the legacy app.
scheduler_store = SchedulerStore("runtime_data/coding_scheduler.sqlite3")

app = FastAPI(
    title="Ailovanta Coding",
    version="2.0.0",
    description="Unified local coding assistant plus opt-in distributed compute control plane.",
)
app.include_router(build_coding_product_router())
app.include_router(build_coding_router(scheduler_store))
app.include_router(build_network_router(scheduler_store))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _front_page() -> Path:
    mode = os.getenv("AILOVANTA_RUNTIME_MODE", "server-local").strip().lower()
    return BASE_DIR / ("control.html" if mode == "control-plane" else "coding.html")


@app.get("/")
@app.get("/app")
def coding_app() -> FileResponse:
    path = _front_page()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    return FileResponse(path)
