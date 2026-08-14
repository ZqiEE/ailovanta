from __future__ import annotations

from pathlib import Path
from typing import Any


def coding_release_gate(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    blockers: list[str] = []
    checks: dict[str, Any] = {}

    required_files = [
        "coding.html",
        "static/coding.css",
        "static/coding.js",
        "api/product_app.py",
        "api/coding_product_routes.py",
        "api/coding_agent.py",
        "api/project_store.py",
        "api/project_changes.py",
        "api/coding_factory.py",
        "api/coding_autonomous_loop.py",
        "api/coding_benchmark_suite.py",
        "Dockerfile",
        "docker-compose.coding.yml",
    ]
    missing = [path for path in required_files if not (base / path).exists()]
    checks["required_files"] = {"ok": not missing, "missing": missing}
    blockers.extend("missing:" + item for item in missing)

    try:
        from api.product_app import app

        paths = {route.path for route in app.routes}
        required_routes = {
            "/",
            "/app",
            "/coding/status",
            "/coding/projects",
        }
        missing_routes = sorted(required_routes - paths)
        checks["routes"] = {"ok": not missing_routes, "missing": missing_routes}
        blockers.extend("missing_route:" + item for item in missing_routes)
    except Exception as exc:
        checks["routes"] = {"ok": False, "error": str(exc)}
        blockers.append("product_app_import_failed")

    dockerfile = (base / "Dockerfile").read_text(encoding="utf-8") if (base / "Dockerfile").exists() else ""
    docker_ok = "api.product_app:app" in dockerfile and "AILOVANTA_ENV=production" in dockerfile
    checks["production_entrypoint"] = {"ok": docker_ok}
    if not docker_ok:
        blockers.append("production_entrypoint_not_coding_product")

    training_text = (base / "api/coding_factory.py").read_text(encoding="utf-8") if (base / "api/coding_factory.py").exists() else ""
    training_ok = all(marker in training_text for marker in ("frontend", "backend", "repair", "coding_unify"))
    checks["training_architecture"] = {"ok": training_ok}
    if not training_ok:
        blockers.append("coding_training_architecture_incomplete")

    return {
        "ok": not blockers,
        "stage": "coding_release_pass" if not blockers else "coding_release_blocked",
        "blockers": sorted(set(blockers)),
        "checks": checks,
    }
