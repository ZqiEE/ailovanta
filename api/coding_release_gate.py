from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "coding.html",
    "control.html",
    "static/coding.css",
    "static/coding.js",
    "static/import_project.js",
    "static/privacy_status.js",
    "start-local.sh",
    "start-local.ps1",
    "requirements-coding.txt",
    "Dockerfile",
    "docker-compose.control.yml",
    "api/product_app.py",
    "api/coding_product_routes.py",
    "api/coding_agent.py",
    "api/project_store.py",
    "api/project_changes.py",
    "api/network_routes.py",
    "api/coding_factory.py",
    "api/coding_autonomous_loop.py",
    "api/coding_benchmark_suite.py",
    "node_client/local_runtime.py",
    "node_client/client_real.py",
    "node_client/coding_inference_worker.py",
)


def _run(base: Path, code: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        cwd=base,
        env=merged,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-3000:],
        "stderr": proc.stderr[-3000:],
    }


def coding_release_gate(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    blockers: list[str] = []
    checks: dict[str, Any] = {}

    missing = [path for path in REQUIRED_FILES if not (base / path).exists()]
    checks["required_files"] = {"ok": not missing, "missing": missing}
    blockers.extend("missing:" + item for item in missing)

    local_code = r'''
from api.product_app import app
paths = {route.path for route in app.routes}
required = {
    "/", "/app", "/coding/status", "/coding/privacy", "/coding/cost", "/coding/projects",
    "/coding/projects/{project_id}/propose", "/coding/projects/{project_id}/apply",
    "/nodes/register", "/jobs/next", "/jobs/result",
}
missing = required - paths
assert not missing, sorted(missing)
print("private-local product surface ready")
'''
    checks["local_product"] = _run(base, local_code, {"AILOVANTA_RUNTIME_MODE": "private-local"})
    if not checks["local_product"]["ok"]:
        blockers.append("local_product_surface_failed")

    control_code = r'''
from api.product_app import app, _front_page
from api.cost_guard import zero_cash_status
paths = {route.path for route in app.routes}
assert _front_page().name == "control.html"
assert "/control/status" in paths
assert "/nodes/register" in paths
assert "/network/status" in paths
assert "/jobs/public-inference" in paths
assert "/coding/projects" not in paths
assert "/coding/status" not in paths
assert "/coding/training/expert" not in paths
cost = zero_cash_status()
assert cost["runtime_mode"] == "control-plane"
assert cost["required_external_model_apis"] == []
print("zero-GPU control plane isolated")
'''
    checks["control_plane"] = _run(
        base,
        control_code,
        {
            "AILOVANTA_RUNTIME_MODE": "control-plane",
            "AILOVANTA_ZERO_CASH_MODE": "true",
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "GEMINI_API_KEY": "",
            "GOOGLE_API_KEY": "",
        },
    )
    if not checks["control_plane"]["ok"]:
        blockers.append("control_plane_isolation_failed")

    launcher_code = r'''
from node_client.local_runtime import main
from node_client.model_profile import recommend_local_model
from node_client.coding_inference_worker import ALLOWED_NETWORK_PRIVACY_SCOPES
assert ALLOWED_NETWORK_PRIVACY_SCOPES == {"public", "synthetic"}
print("local launcher and community worker privacy policy import")
'''
    checks["local_launcher"] = _run(base, launcher_code)
    if not checks["local_launcher"]["ok"]:
        blockers.append("local_launcher_import_failed")

    network_code = r'''
from api.network_routes import PublicInferenceRequest
from pydantic import ValidationError
try:
    PublicInferenceRequest(prompt="private", privacy_scope="private")
except ValidationError:
    pass
else:
    raise AssertionError("private public-inference scope accepted")
print("private scope impossible on public inference schema")
'''
    checks["network_privacy"] = _run(base, network_code, {"AILOVANTA_PUBLIC_INFERENCE_TOKEN": ""})
    if not checks["network_privacy"]["ok"]:
        blockers.append("network_privacy_gate_failed")

    dockerfile = (base / "Dockerfile").read_text(encoding="utf-8") if (base / "Dockerfile").exists() else ""
    docker_ok = "requirements-coding.txt" in dockerfile and "api.product_app:app" in dockerfile
    checks["lean_production_entrypoint"] = {"ok": docker_ok}
    if not docker_ok:
        blockers.append("production_entrypoint_not_lean_coding_product")

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
