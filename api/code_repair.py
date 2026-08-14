from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.autotruth_store import AutoTruthEventStore

ALLOWED_TEST_COMMANDS = {"pytest", "python -m pytest", "npm test"}
ALLOWED_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt"}


class CodeRepairError(ValueError):
    pass


def check_command(command: str) -> list[str]:
    command = command.strip()
    if command not in ALLOWED_TEST_COMMANDS:
        raise CodeRepairError("test command is not allowed")
    if command in {"pytest", "python -m pytest"}:
        return [sys.executable, "-m", "pytest"]
    return shlex.split(command)


def run_test(command: str, project_dir: str | Path, timeout: int = 120) -> dict[str, Any]:
    root = Path(project_dir).resolve()
    args = check_command(command)
    if command in {"pytest", "python -m pytest"}:
        args = [*args, "-q", "--rootdir", str(root), str(root)]
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(root) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    proc = subprocess.run(args, cwd=str(root), text=True, capture_output=True, timeout=timeout, env=env)
    return {"command": command, "returncode": proc.returncode, "ok": proc.returncode == 0, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:]}


def safe_path(project_dir: str | Path, relative_path: str) -> Path:
    root = Path(project_dir).resolve()
    target = (root / relative_path).resolve()
    if root not in [target, *target.parents]:
        raise CodeRepairError("path outside project")
    if target.suffix not in ALLOWED_SUFFIXES:
        raise CodeRepairError("file suffix not allowed")
    return target


def apply_replacements(project_dir: str | Path, replacements: list[dict[str, str]]) -> list[dict[str, Any]]:
    changed = []
    for item in replacements:
        target = safe_path(project_dir, item["path"])
        old = item["old"]
        new = item["new"]
        text = target.read_text(encoding="utf-8")
        if old not in text:
            raise CodeRepairError("old text not found")
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        changed.append({"path": item["path"], "old_len": len(old), "new_len": len(new)})
    return changed


def repair_prompt(test_result: dict[str, Any], project_hint: str = "") -> str:
    return "\n".join([
        "Fix the project so the tests pass.",
        "Return JSON replacements only: [{path, old, new}]",
        project_hint,
        "STDOUT:",
        test_result.get("stdout", ""),
        "STDERR:",
        test_result.get("stderr", ""),
    ])


def record_success(task_id: str, prompt: str, replacements: list[dict[str, str]], before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return AutoTruthEventStore().add_event({
        "input": prompt,
        "output": json.dumps({"replacements": replacements}, ensure_ascii=False),
        "source": "ailovanta-code-repair",
        "behavior": {"score": 1.0, "test_before": before["returncode"], "test_after": after["returncode"]},
        "metadata": {"task_id": task_id, "verified": True, "created_at": round(time(), 3)},
    })


def verified_repair(project_dir: str | Path, test_command: str, replacements: list[dict[str, str]] | None = None, project_hint: str = "") -> dict[str, Any]:
    task_id = "repair_" + uuid4().hex[:12]
    before = run_test(test_command, project_dir)
    prompt = repair_prompt(before, project_hint=project_hint)
    if before["ok"]:
        return {"ok": True, "stage": "already_passing", "task_id": task_id, "before": before, "prompt": prompt}
    if replacements is None:
        return {"ok": False, "stage": "needs_repair", "task_id": task_id, "before": before, "prompt": prompt}
    changed = apply_replacements(project_dir, replacements)
    after = run_test(test_command, project_dir)
    event = record_success(task_id, prompt, replacements, before, after) if after["ok"] else None
    return {"ok": after["ok"], "stage": "repair_verified" if after["ok"] else "repair_failed", "task_id": task_id, "changed": changed, "before": before, "after": after, "training_event": event}
