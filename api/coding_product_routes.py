from __future__ import annotations

import io
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.coding_agent import CodingAgent, CodingAgentError
from api.cost_guard import zero_cash_status
from api.model_status import coding_model_status
from api.project_changes import apply_changes, project_diff
from api.project_store import ProjectStore, ProjectStoreError


class CreateProjectRequest(BaseModel):
    owner: str = "guest"
    name: str = "Untitled project"


class FileWriteRequest(BaseModel):
    path: str
    content: str


class ImportFilesRequest(BaseModel):
    files: list[FileWriteRequest]
    source_url: str | None = None


class ProposeRequest(BaseModel):
    task: str = Field(min_length=1, max_length=12000)
    mode: str = "auto"


class ApplyRequest(BaseModel):
    changes: list[dict[str, Any]]


def build_coding_product_router(store: ProjectStore | None = None) -> APIRouter:
    projects = store or ProjectStore()
    agent = CodingAgent(store=projects)
    router = APIRouter(prefix="/coding", tags=["coding-product"])

    @router.get("/status")
    def status() -> dict[str, Any]:
        model_state = coding_model_status(agent.model)
        return {
            "ok": bool(model_state.get("available") and model_state.get("model_present")),
            "product": "Ailovanta Coding",
            "model": agent.model.config.model,
            "model_runtime": model_state,
            "cost": zero_cash_status(),
            "modes": ["auto", "frontend", "backend", "repair"],
            "max_files": projects.max_files,
            "max_project_bytes": projects.max_project_bytes,
        }

    @router.get("/cost")
    def cost_status() -> dict[str, Any]:
        return zero_cash_status()

    @router.post("/projects")
    def create_project(body: CreateProjectRequest) -> dict[str, Any]:
        return projects.create(body.owner, body.name)

    @router.get("/projects")
    def list_projects(owner: str = "guest") -> dict[str, Any]:
        return {"projects": projects.list(owner)}

    @router.get("/projects/{project_id}")
    def get_project(project_id: str, owner: str) -> dict[str, Any]:
        return _owned(projects, project_id, owner)

    @router.get("/projects/{project_id}/file")
    def read_file(project_id: str, path: str, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        return _call(projects.read_file, project_id, path)

    @router.put("/projects/{project_id}/file")
    def write_file(project_id: str, body: FileWriteRequest, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        return _call(projects.put_file, project_id, body.path, body.content)

    @router.delete("/projects/{project_id}/file")
    def delete_file(project_id: str, path: str, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        return _call(projects.delete_file, project_id, path)

    @router.post("/projects/{project_id}/import")
    def import_files(project_id: str, body: ImportFilesRequest, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        try:
            if not body.files or len(body.files) > projects.max_files:
                raise ProjectStoreError("invalid import file count")
            projects.reset_files(project_id)
            total = 0
            for row in body.files:
                raw = row.content.encode("utf-8")
                total += len(raw)
                if len(raw) > projects.max_file_bytes or total > projects.max_project_bytes:
                    raise ProjectStoreError("import exceeds project limits")
                projects.seed_file(project_id, row.path, row.content)
            return projects.update_meta(project_id, source="github" if body.source_url else "import", source_url=body.source_url)
        except ProjectStoreError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/projects/{project_id}/propose")
    def propose(project_id: str, body: ProposeRequest, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        try:
            return agent.propose(project_id, body.task, body.mode)
        except (CodingAgentError, ProjectStoreError) as exc:
            message = str(exc)
            status_code = 503 if "unavailable" in message else 400
            raise HTTPException(status_code=status_code, detail=message) from exc

    @router.post("/projects/{project_id}/apply")
    def apply(project_id: str, body: ApplyRequest, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        try:
            return apply_changes(projects, project_id, body.changes)
        except ProjectStoreError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/projects/{project_id}/diff")
    def diff(project_id: str, owner: str) -> dict[str, Any]:
        _owned(projects, project_id, owner)
        try:
            return {"project_id": project_id, "diff": project_diff(projects, project_id)}
        except ProjectStoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/projects/{project_id}/export")
    def export(project_id: str, owner: str) -> StreamingResponse:
        _owned(projects, project_id, owner)
        try:
            data = projects.export_zip(project_id)
        except ProjectStoreError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        headers = {"Content-Disposition": f'attachment; filename="{project_id}.zip"'}
        return StreamingResponse(io.BytesIO(data), media_type="application/zip", headers=headers)

    return router


def _owned(projects: ProjectStore, project_id: str, owner: str) -> dict[str, Any]:
    project = _call(projects.get, project_id)
    if not owner or project.get("owner") != owner:
        raise HTTPException(status_code=404, detail="project not found")
    return project


def _call(fn, *args):
    try:
        return fn(*args)
    except ProjectStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
