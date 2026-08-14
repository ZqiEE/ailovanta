from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from api.project_store import ProjectStore, ProjectStoreError
from api.project_validator import validate_changes


def _preflight_changes(store: ProjectStore, project_id: str, changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not changes:
        raise ProjectStoreError("changeset is empty")
    if len(changes) > 32:
        raise ProjectStoreError("too many file changes")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    current = {item["path"]: int(item["bytes"]) for item in store.list_files(project_id)}

    for change in changes:
        if not isinstance(change, dict):
            raise ProjectStoreError("invalid file change")
        rel = store.safe_path(str(change.get("path") or "")).as_posix()
        if rel in seen:
            raise ProjectStoreError("changeset contains duplicate path: " + rel)
        seen.add(rel)
        if change.get("delete") is True:
            normalized.append({"path": rel, "delete": True})
            current.pop(rel, None)
            continue
        if "content" not in change:
            raise ProjectStoreError("file change missing content")
        content = str(change.get("content") or "")
        raw_size = len(content.encode("utf-8"))
        if raw_size > store.max_file_bytes:
            raise ProjectStoreError("generated file exceeds size limit: " + rel)
        normalized.append({"path": rel, "content": content})
        current[rel] = raw_size

    if len(current) > store.max_files:
        raise ProjectStoreError("changeset would exceed project file limit")
    if sum(current.values()) > store.max_project_bytes:
        raise ProjectStoreError("changeset would exceed project size limit")
    return normalized


def apply_changes(store: ProjectStore, project_id: str, changes: list[dict[str, Any]]) -> dict[str, Any]:
    store.get(project_id)
    normalized = _preflight_changes(store, project_id, changes)
    validation = validate_changes(normalized)
    if not validation.get("ok"):
        first = validation["diagnostics"][0]
        raise ProjectStoreError(
            "generated changes failed static validation: "
            + str(first.get("path"))
            + ": "
            + str(first.get("message"))
        )

    # At 16MB default project size it is cheap and reliable to remember only the
    # touched files. This lets us restore the exact pre-apply state if any disk or
    # validation error occurs midway through a batch.
    before: dict[str, str | None] = {}
    for change in normalized:
        path = change["path"]
        try:
            before[path] = store.read_file(project_id, path)["content"]
        except ProjectStoreError as exc:
            if str(exc) != "file not found":
                raise
            before[path] = None

    applied: list[dict[str, Any]] = []
    try:
        # Deletions first make room for replacements elsewhere in a batch whose
        # final projected size is valid even if the pre-delete state is near limit.
        for change in normalized:
            if change.get("delete") is not True:
                continue
            path = change["path"]
            try:
                applied.append(store.delete_file(project_id, path))
            except ProjectStoreError as exc:
                if str(exc) != "file not found":
                    raise
                applied.append({"ok": True, "path": path, "already_missing": True})
        for change in normalized:
            if change.get("delete") is True:
                continue
            applied.append(store.put_file(project_id, change["path"], change["content"]))
    except Exception:
        _restore_touched_files(store, project_id, before)
        raise

    return {
        "ok": True,
        "applied": applied,
        "validation": validation,
        "diff": project_diff(store, project_id),
    }


def _restore_touched_files(store: ProjectStore, project_id: str, before: dict[str, str | None]) -> None:
    for path, content in before.items():
        target = Path(store.root) / project_id / "files" / store.safe_path(path)
        if content is None:
            if target.exists():
                target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    try:
        store.update_meta(project_id)
    except Exception:
        pass


def project_diff(store: ProjectStore, project_id: str) -> str:
    store.get(project_id)
    project_root = Path(store.root) / project_id
    current_root = project_root / "files"
    original_root = project_root / "original"
    paths: set[str] = set()
    for root in (current_root, original_root):
        if root.exists():
            paths.update(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    chunks: list[str] = []
    for rel in sorted(paths):
        current = current_root / rel
        original = original_root / rel
        before = original.read_text(encoding="utf-8", errors="replace").splitlines(True) if original.exists() else []
        after = current.read_text(encoding="utf-8", errors="replace").splitlines(True) if current.exists() else []
        if before == after:
            continue
        chunks.extend(difflib.unified_diff(before, after, fromfile="a/" + rel, tofile="b/" + rel))
    return "".join(chunks)
