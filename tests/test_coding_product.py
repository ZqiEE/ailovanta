from pathlib import Path

import pytest

from api.coding_agent import CodingAgent
from api.project_changes import apply_changes, project_diff
from api.project_store import ProjectStore, ProjectStoreError


class FakeConfig:
    model = "ailovanta-test"


class FakeModel:
    config = FakeConfig()

    def chat_messages(self, messages, mode="open", memory=None):
        assert mode == "coding"
        assert "hello.py" in messages[0]["content"]
        return '{"summary":"fix greeting","explanation":"updated output","changes":[{"path":"hello.py","content":"print(\\"hello world\\")\\n"}]}'


def test_project_edit_diff_export(tmp_path: Path):
    store = ProjectStore(tmp_path)
    project = store.create("guest-test", "Example")
    project_id = project["project_id"]
    store.put_file(project_id, "hello.py", 'print("hello")\n')
    result = apply_changes(store, project_id, [{"path": "hello.py", "content": 'print("hello world")\n'}])
    assert result["ok"] is True
    assert "+print(\"hello world\")" in project_diff(store, project_id)
    assert len(store.export_zip(project_id)) > 20


def test_unified_agent_proposes_real_file_changes(tmp_path: Path):
    store = ProjectStore(tmp_path)
    project_id = store.create("guest-test", "Example")["project_id"]
    store.put_file(project_id, "hello.py", 'print("hello")\n')
    agent = CodingAgent(store=store, model=FakeModel())
    proposal = agent.propose(project_id, "Improve the greeting", "repair")
    assert proposal["model"] == "ailovanta-test"
    assert proposal["changes"][0]["path"] == "hello.py"
    apply_changes(store, project_id, proposal["changes"])
    assert "hello world" in store.read_file(project_id, "hello.py")["content"]


def test_project_paths_cannot_escape_workspace(tmp_path: Path):
    store = ProjectStore(tmp_path)
    project_id = store.create("guest-test", "Example")["project_id"]
    with pytest.raises(ProjectStoreError):
        store.put_file(project_id, "../outside.py", "bad")
