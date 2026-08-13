from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.coding_product_routes import build_coding_product_router
from api.coding_routes import build_coding_router
from api.main import app as legacy_app
from api.main import store as scheduler_store


BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Ailovanta Coding",
    version="2.0.0",
    description="Unified coding assistant with project workspaces and autonomous training infrastructure.",
)
app.include_router(build_coding_product_router())
app.include_router(build_coding_router(scheduler_store))
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
@app.get("/app")
def coding_app() -> FileResponse:
    path = BASE_DIR / "coding.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="coding.html not found")
    return FileResponse(path)


@app.get("/legacy-app")
def legacy_public_app() -> FileResponse:
    path = BASE_DIR / "index.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(path)


app.mount("/", legacy_app)
