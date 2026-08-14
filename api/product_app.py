from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.coding_product_routes import build_coding_product_router
from api.coding_routes import build_coding_router
from api.cost_guard import zero_cash_status
from api.network_routes import build_network_router
from api.storage import SchedulerStore


BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
RUNTIME_MODE = os.getenv("AILOVANTA_RUNTIME_MODE", "server-local").strip().lower() or "server-local"

scheduler_store = SchedulerStore("runtime_data/coding_scheduler.sqlite3")

app = FastAPI(
    title="Ailovanta Coding",
    version="2.0.0",
    description="Private local coding assistant plus opt-in distributed compute control plane.",
)

# Private project/code endpoints do not exist on the public control-plane process.
# They are registered only on the user's local runtime (or an explicitly chosen
# server-local fallback). This prevents accidental private-repo uploads to the
# public domain even if a client calls a private endpoint directly.
if RUNTIME_MODE != "control-plane":
    app.include_router(build_coding_product_router())
    app.include_router(build_coding_router(scheduler_store))

# Distributed worker/control routes are lightweight and are present in both
# modes, so a local developer can test the network without a second app.
app.include_router(build_network_router(scheduler_store))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/control/status")
def control_status() -> dict:
    status = scheduler_store.status()
    return {
        "ok": True,
        "runtime_mode": RUNTIME_MODE,
        "network": {
            "nodes": status.get("nodes", 0),
            "queued_jobs": status.get("queued_jobs", 0),
            "assigned_jobs": status.get("assigned_jobs", 0),
        },
        "cost": zero_cash_status(),
    }


def _front_page() -> Path:
    return BASE_DIR / ("control.html" if RUNTIME_MODE == "control-plane" else "coding.html")


@app.get("/")
@app.get("/app")
def coding_app() -> FileResponse:
    path = _front_page()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    return FileResponse(path)
