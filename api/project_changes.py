from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from api.project_store import ProjectStore, ProjectStoreError
from api.project_validator import validate_changes


def apply_changes(store: ProjectStore, project_id: str, changes: list[dict[str, Any]]) -> dict[str, Any]:
    if len(changes) > 32:
        raise ProjectStoreError("too many file changes")

    validation = validate_changes(changes)
    if not validation.get("ok"):
        first = validation["diagnostics"][0]
        raise ProjectStoreError(
            "generated changes failed static validation: "
            + str(first.get("path"))
            + ": "
            + str(first.get("message"))
        )

    applied = []
    for change in changes:
        path = str(change.get("path") or "")
        if change.get("delete") is True:
            try:
                applied.append(store.delete_file(project_id, path))
            except ProjectStoreError as exc:
                if str(exc) != "file not found":
                    raise
                applied.append({"ok": True, "path": path, "already_missing": True})
        else:
            if "content" not in change:
                raise ProjectStoreError("file change missing content")
            applied.append(store.put_file(project_id, path, str(change.get("content") or "")))
    return {
        "ok": True,
        "applied": applied,
        "validation": validation,
        "diff": project_diff(store, project_id),
    }


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
