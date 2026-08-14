from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path, PurePosixPath
from time import time
from typing import Any
from uuid import uuid4


class ProjectStoreError(ValueError):
    pass


class ProjectStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv("AILOVANTA_PROJECT_ROOT", "runtime_data/coding_projects"))
        # Local-first defaults: large enough for real source projects after
        # generated/vendor directories are filtered, still bounded against accidents.
        self.max_files = int(os.getenv("AILOVANTA_PROJECT_MAX_FILES", "512"))
        self.max_file_bytes = int(os.getenv("AILOVANTA_PROJECT_MAX_FILE_BYTES", str(512 * 1024)))
        self.max_project_bytes = int(os.getenv("AILOVANTA_PROJECT_MAX_BYTES", str(16 * 1024 * 1024)))
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, owner: str, name: str) -> dict[str, Any]:
        project_id = "proj_" + uuid4().hex[:12]
        (self._root(project_id) / "files").mkdir(parents=True)
        (self._root(project_id) / "original").mkdir(parents=True)
        meta = {
            "project_id": project_id,
            "owner": (owner or "guest")[:120],
            "name": (name.strip() or "Untitled project")[:120],
            "source": "manual",
            "source_url": None,
            "created_at": round(time(), 3),
            "updated_at": round(time(), 3),
        }
        self._save_meta(project_id, meta)
        return self.get(project_id)

    def list(self, owner: str | None = None) -> list[dict[str, Any]]:
        rows = []
        for path in self.root.glob("*/project.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if owner is not None and item.get("owner") != owner:
                continue
            item["file_count"] = len(self.list_files(item["project_id"]))
            rows.append(item)
        return sorted(rows, key=lambda item: float(item.get("updated_at", 0)), reverse=True)

    def get(self, project_id: str) -> dict[str, Any]:
        path = self._root(project_id) / "project.json"
        if not path.exists():
            raise ProjectStoreError("project not found")
        item = json.loads(path.read_text(encoding="utf-8"))
        item["files"] = self.list_files(project_id)
        item["file_count"] = len(item["files"])
        return item

    def update_meta(self, project_id: str, **changes: Any) -> dict[str, Any]:
        item = self.get(project_id)
        item.pop("files", None)
        item.pop("file_count", None)
        item.update(changes)
        item["updated_at"] = round(time(), 3)
        self._save_meta(project_id, item)
        return self.get(project_id)

    def list_files(self, project_id: str) -> list[dict[str, Any]]:
        root = self._files(project_id)
        if not root.exists():
            return []
        rows = []
        for path in root.rglob("*"):
            if path.is_file():
                rows.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size})
        return sorted(rows, key=lambda item: item["path"])

    def read_file(self, project_id: str, path: str) -> dict[str, str]:
        rel = self.safe_path(path)
        target = self._files(project_id) / rel
        if not target.is_file():
            raise ProjectStoreError("file not found")
        return {"path": rel.as_posix(), "content": target.read_text(encoding="utf-8", errors="replace")}

    def preflight_write(self, project_id: str, path: str, content: str) -> PurePosixPath:
        self.get(project_id)
        rel = self.safe_path(path)
        raw = content.encode("utf-8")
        if len(raw) > self.max_file_bytes:
            raise ProjectStoreError("file exceeds size limit")
        files = self.list_files(project_id)
        existing = next((item for item in files if item["path"] == rel.as_posix()), None)
        projected_count = len(files) + (0 if existing else 1)
        projected_bytes = sum(int(item["bytes"]) for item in files) - int(existing["bytes"] if existing else 0) + len(raw)
        if projected_count > self.max_files:
            raise ProjectStoreError("project has too many files")
        if projected_bytes > self.max_project_bytes:
            raise ProjectStoreError("project exceeds size limit")
        return rel

    def put_file(self, project_id: str, path: str, content: str, snapshot_new: bool = True) -> dict[str, str]:
        rel = self.preflight_write(project_id, path, content)
        target = self._files(project_id) / rel
        original = self._original(project_id) / rel
        if snapshot_new and not target.exists() and not original.exists():
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_text("", encoding="utf-8")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.update_meta(project_id)
        return self.read_file(project_id, rel.as_posix())

    def seed_file(self, project_id: str, path: str, content: str) -> None:
        rel = self.safe_path(path)
        raw = content.encode("utf-8")
        if len(raw) > self.max_file_bytes:
            raise ProjectStoreError("file exceeds size limit")
        for root in (self._files(project_id), self._original(project_id)):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def delete_file(self, project_id: str, path: str) -> dict[str, Any]:
        rel = self.safe_path(path)
        target = self._files(project_id) / rel
        if not target.exists():
            raise ProjectStoreError("file not found")
        target.unlink()
        self.update_meta(project_id)
        return {"ok": True, "path": rel.as_posix()}

    def reset_files(self, project_id: str) -> None:
        for root in (self._files(project_id), self._original(project_id)):
            if not root.exists():
                root.mkdir(parents=True)
                continue
            for path in sorted(root.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    try:
                        path.rmdir()
                    except OSError:
                        pass

    def export_zip(self, project_id: str) -> bytes:
        self.get(project_id)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for item in self.list_files(project_id):
                archive.writestr(item["path"], self.read_file(project_id, item["path"])["content"])
        return output.getvalue()

    def context(self, project_id: str, max_chars: int = 160000) -> str:
        parts: list[str] = []
        remaining = max_chars
        for item in self.list_files(project_id):
            content = self.read_file(project_id, item["path"])["content"]
            block = f"\n--- FILE: {item['path']} ---\n{content}\n--- END FILE ---\n"
            if len(block) > remaining:
                block = block[:remaining]
            parts.append(block)
            remaining -= len(block)
            if remaining <= 0:
                break
        return "".join(parts)

    @staticmethod
    def safe_path(path: str) -> PurePosixPath:
        clean = path.replace("\\", "/").strip()
        rel = PurePosixPath(clean)
        if not clean or rel.is_absolute() or ".." in rel.parts or len(clean) > 300 or len(rel.parts) > 24:
            raise ProjectStoreError("invalid file path")
        return rel

    def _check_limits(self, project_id: str) -> None:
        files = self.list_files(project_id)
        if len(files) > self.max_files:
            raise ProjectStoreError("project has too many files")
        if sum(item["bytes"] for item in files) > self.max_project_bytes:
            raise ProjectStoreError("project exceeds size limit")

    def _save_meta(self, project_id: str, item: dict[str, Any]) -> None:
        path = self._root(project_id) / "project.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")

    def _root(self, project_id: str) -> Path:
        if not project_id.startswith("proj_") or not project_id.replace("_", "").isalnum():
            raise ProjectStoreError("invalid project id")
        return self.root / project_id

    def _files(self, project_id: str) -> Path:
        return self._root(project_id) / "files"

    def _original(self, project_id: str) -> Path:
        return self._root(project_id) / "original"
