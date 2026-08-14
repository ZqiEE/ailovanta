from __future__ import annotations

from pathlib import Path

import pytest

from api.local_workspace import LocalWorkspaceConflict, open_local_workspace, sync_local_workspace
from api.project_changes import project_diff
from api.project_store import ProjectStore


def test_open_local_workspace_imports_source_and_skips_generated_dirs(tmp_path: Path):
    source = tmp_path / "repo"
    source.mkdir()
    (source / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (source / "node_modules").mkdir()
    (source / "node_modules" / "ignored.js").write_text("bad()", encoding="utf-8")

    store = ProjectStore(tmp_path / "runtime")
    project = open_local_workspace(store, source, owner="local")
    assert project["workspace_open"] == "created"
    assert project["source"] == "local-path"
    assert project["source_path"] == str(source.resolve())
    assert store.read_file(project["project_id"], "app.py")["content"] == "print('hello')\n"
    assert {item["path"] for item in store.list_files(project["project_id"])} == {"app.py"}


def test_clean_linked_workspace_refreshes_from_disk_but_dirty_workspace_is_preserved(tmp_path: Path):
    source = tmp_path / "repo"
    source.mkdir()
    target = source / "app.py"
    target.write_text("v1\n", encoding="utf-8")
    store = ProjectStore(tmp_path / "runtime")

    project = open_local_workspace(store, source, owner="local")
    project_id = project["project_id"]

    target.write_text("v2\n", encoding="utf-8")
    refreshed = open_local_workspace(store, source, owner="local")
    assert refreshed["project_id"] == project_id
    assert refreshed["workspace_open"] == "refreshed_from_disk"
    assert store.read_file(project_id, "app.py")["content"] == "v2\n"

    store.put_file(project_id, "app.py", "ailovanta-change\n")
    target.write_text("human-change\n", encoding="utf-8")
    reopened = open_local_workspace(store, source, owner="local")
    assert reopened["workspace_open"] == "reused_unsynced_changes"
    assert store.read_file(project_id, "app.py")["content"] == "ailovanta-change\n"


def test_sync_updates_creates_deletes_backs_up_and_resets_diff(tmp_path: Path):
    source = tmp_path / "repo"
    source.mkdir()
    (source / "app.py").write_text("old\n", encoding="utf-8")
    (source / "remove.py").write_text("remove me\n", encoding="utf-8")
    store = ProjectStore(tmp_path / "runtime")
    project = open_local_workspace(store, source, owner="local")
    project_id = project["project_id"]

    store.put_file(project_id, "app.py", "new\n")
    store.put_file(project_id, "new_file.py", "created\n")
    store.delete_file(project_id, "remove.py")
    assert project_diff(store, project_id)

    result = sync_local_workspace(store, project_id)
    assert result["ok"] is True
    assert set(result["synced"]) == {"app.py", "new_file.py", "remove.py"}
    assert (source / "app.py").read_text(encoding="utf-8") == "new\n"
    assert (source / "new_file.py").read_text(encoding="utf-8") == "created\n"
    assert not (source / "remove.py").exists()
    assert result["backup_dir"] is not None
    backup = Path(result["backup_dir"])
    assert (backup / "app.py").read_text(encoding="utf-8") == "old\n"
    assert (backup / "remove.py").read_text(encoding="utf-8") == "remove me\n"
    assert project_diff(store, project_id) == ""


def test_sync_aborts_entire_batch_when_source_changed_outside_ailovanta(tmp_path: Path):
    source = tmp_path / "repo"
    source.mkdir()
    target = source / "app.py"
    target.write_text("baseline\n", encoding="utf-8")
    store = ProjectStore(tmp_path / "runtime")
    project = open_local_workspace(store, source, owner="local")
    project_id = project["project_id"]

    store.put_file(project_id, "app.py", "ai version\n")
    store.put_file(project_id, "new_file.py", "should not sync\n")
    target.write_text("human version\n", encoding="utf-8")

    with pytest.raises(LocalWorkspaceConflict) as exc_info:
        sync_local_workspace(store, project_id)
    assert "app.py" in exc_info.value.conflicts
    assert target.read_text(encoding="utf-8") == "human version\n"
    assert not (source / "new_file.py").exists()
    assert project_diff(store, project_id)
