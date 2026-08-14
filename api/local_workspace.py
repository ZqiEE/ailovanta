from __future__ import annotations

import os
from pathlib import Path
from time import time
from typing import Any

from api.project_store import ProjectStore, ProjectStoreError


IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build",
    "target", "vendor", ".next", ".nuxt", "coverage", "__pycache__", ".idea", ".vscode",
}
SUPPORTED_NAMES = {"Dockerfile", "Makefile", "Procfile", ".gitignore", ".env.example", "LICENSE"}
SUPPORTED_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".htm", ".css",
    ".scss", ".md", ".mdx", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".txt", ".sql",
    ".sh", ".java", ".kt", ".go", ".rs", ".c", ".h", ".cpp", ".hpp", ".cs", ".php",
    ".rb", ".swift", ".vue", ".svelte", ".xml", ".graphql", ".gql", ".proto",
}


class LocalWorkspaceConflict(ProjectStoreError):
    def __init__(self, conflicts: list[str]) -> None:
        self.conflicts = conflicts
        super().__init__("local workspace changed outside Ailovanta: " + ", ".join(conflicts[:8]))


def _supported(path: Path) -> bool:
    return path.name in SUPPORTED_NAMES or path.suffix.lower() in SUPPORTED_SUFFIXES


def _inside(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_source_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ProjectStoreError("local project directory not found")
    return root


def _collect_source(store: ProjectStore, source: Path) -> tuple[list[tuple[str, str]], int, int]:
    selected: list[tuple[str, str]] = []
    total_bytes = 0
    skipped = 0
    for current_root, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRS]
        base = Path(current_root)
        for filename in files:
            path = base / filename
            if path.is_symlink() or not _supported(path):
                skipped += 1
                continue
            try:
                rel = path.relative_to(source).as_posix()
                safe_rel = store.safe_path(rel).as_posix()
                raw = path.read_bytes()
                text = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError, ProjectStoreError):
                skipped += 1
                continue
            if len(raw) > store.max_file_bytes:
                skipped += 1
                continue
            if len(selected) >= store.max_files or total_bytes + len(raw) > store.max_project_bytes:
                skipped += 1
                continue
            total_bytes += len(raw)
            selected.append((safe_rel, text))
    if not selected:
        raise ProjectStoreError("no supported UTF-8 source files found in local project")
    return selected, total_bytes, skipped


def _workspace_dirty(store: ProjectStore, project_id: str) -> bool:
    current_root = Path(store.root) / project_id / "files"
    original_root = Path(store.root) / project_id / "original"
    paths: set[str] = set()
    for root in (current_root, original_root):
        if root.exists():
            paths.update(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    for rel in paths:
        current = current_root / store.safe_path(rel)
        original = original_root / store.safe_path(rel)
        after = current.read_bytes() if current.exists() else None
        before = original.read_bytes() if original.exists() else None
        if after != before:
            return True
    return False


def _replace_workspace_from_source(
    store: ProjectStore,
    project_id: str,
    selected: list[tuple[str, str]],
) -> None:
    store.reset_files(project_id)
    for rel, content in selected:
        store.seed_file(project_id, rel, content)


def import_local_workspace(
    store: ProjectStore,
    source_path: str | Path,
    *,
    owner: str = "local",
    name: str | None = None,
) -> dict[str, Any]:
    source = _safe_source_root(source_path)
    selected, total_bytes, skipped = _collect_source(store, source)
    project = store.create(owner, name or source.name or "Local project")
    project_id = project["project_id"]
    _replace_workspace_from_source(store, project_id, selected)
    return store.update_meta(
        project_id,
        source="local-path",
        source_path=str(source),
        imported_files=len(selected),
        skipped_files=skipped,
        imported_bytes=total_bytes,
    )


def open_local_workspace(
    store: ProjectStore,
    source_path: str | Path,
    *,
    owner: str = "local",
) -> dict[str, Any]:
    source = _safe_source_root(source_path)
    source_text = str(source)
    existing = next(
        (
            project
            for project in store.list(owner)
            if project.get("source") == "local-path" and project.get("source_path") == source_text
        ),
        None,
    )
    if not existing:
        result = import_local_workspace(store, source, owner=owner)
        result["workspace_open"] = "created"
        return result

    project_id = str(existing["project_id"])
    if _workspace_dirty(store, project_id):
        result = store.get(project_id)
        result["workspace_open"] = "reused_unsynced_changes"
        return result

    selected, total_bytes, skipped = _collect_source(store, source)
    _replace_workspace_from_source(store, project_id, selected)
    result = store.update_meta(
        project_id,
        imported_files=len(selected),
        skipped_files=skipped,
        imported_bytes=total_bytes,
        refreshed_at=round(time(), 3),
    )
    result["workspace_open"] = "refreshed_from_disk"
    return result


def sync_local_workspace(store: ProjectStore, project_id: str) -> dict[str, Any]:
    project = store.get(project_id)
    if project.get("source") != "local-path" or not project.get("source_path"):
        raise ProjectStoreError("project is not linked to a local directory")
    source = _safe_source_root(str(project["source_path"]))
    current_root = Path(store.root) / project_id / "files"
    original_root = Path(store.root) / project_id / "original"

    paths: set[str] = set()
    for root in (current_root, original_root):
        if root.exists():
            paths.update(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())

    changed: list[tuple[str, bytes | None, bytes | None]] = []
    conflicts: list[str] = []
    for rel in sorted(paths):
        safe_rel = store.safe_path(rel)
        current = current_root / safe_rel
        original = original_root / safe_rel
        after = current.read_bytes() if current.exists() else None
        baseline = original.read_bytes() if original.exists() else None
        if after == baseline:
            continue

        target = source / safe_rel
        resolved_target = target.resolve(strict=False)
        if not _inside(source, resolved_target) or target.is_symlink():
            conflicts.append(rel)
            continue
        disk = target.read_bytes() if target.exists() and target.is_file() else None
        if disk != baseline:
            conflicts.append(rel)
            continue
        changed.append((rel, baseline, after))

    if conflicts:
        raise LocalWorkspaceConflict(conflicts)
    if not changed:
        return {"ok": True, "synced": [], "backup_dir": None, "message": "no changes to sync"}

    stamp = str(int(time() * 1000))
    backup_root = Path(store.root) / project_id / "sync_backups" / stamp
    rollback: dict[str, bytes | None] = {}

    try:
        for rel, _baseline, after in changed:
            safe_rel = store.safe_path(rel)
            target = source / safe_rel
            resolved_target = target.resolve(strict=False)
            if not _inside(source, resolved_target) or target.is_symlink():
                raise LocalWorkspaceConflict([rel])
            before = target.read_bytes() if target.exists() and target.is_file() else None
            rollback[rel] = before
            if before is not None:
                backup = backup_root / safe_rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(before)
            if after is None:
                if target.exists():
                    target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(after)
    except Exception:
        for rel, before in rollback.items():
            target = source / store.safe_path(rel)
            if before is None:
                if target.exists() and target.is_file():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(before)
        raise

    for rel, _baseline, after in changed:
        safe_rel = store.safe_path(rel)
        baseline_path = original_root / safe_rel
        if after is None:
            if baseline_path.exists():
                baseline_path.unlink()
        else:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_bytes(after)

    store.update_meta(project_id, last_synced_at=round(time(), 3))
    return {
        "ok": True,
        "synced": [rel for rel, _baseline, _after in changed],
        "backup_dir": str(backup_root) if backup_root.exists() else None,
        "source_path": str(source),
    }
