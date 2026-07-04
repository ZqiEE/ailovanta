from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.autotruth_store import AutoTruthEventStore

ALLOWED_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt"}


class RepairTaskError(ValueError):
    pass


def make_repair_prompt(test_name: str, stdout: str = "", stderr: str = "", project_hint: str = "") -> str:
    return "\n".join(
        [
            "Ailovanta Code repair task.",
            "Goal: produce a minimal patch so the failing test passes.",
            "Return JSON only: {\"replacements\":[{\"path\":...,\"old\":...,\"new\":...}]}",
            "Do not touch files outside the project.",
            project_hint,
            "TEST:",
            test_name,
            "STDOUT:",
            stdout[-4000:],
            "STDERR:",
            stderr[-4000:],
        ]
    )


def validate_replacements(project_dir: str | Path, replacements: list[dict[str, str]]) -> list[dict[str, Any]]:
    root = Path(project_dir).resolve()
    checked: list[dict[str, Any]] = []
    for item in replacements:
        rel = item.get("path") or ""
        target = (root / rel).resolve()
        if root not in [target, *target.parents]:
            raise RepairTaskError("replacement path outside project")
        if target.suffix not in ALLOWED_SUFFIXES:
            raise RepairTaskError("replacement suffix not allowed")
        old = item.get("old") or ""
        new = item.get("new") or ""
        if not old:
            raise RepairTaskError("replacement old text is empty")
        checked.append({"path": rel, "old_len": len(old), "new_len": len(new)})
    return checked


def record_verified_repair(prompt: str, replacements: list[dict[str, str]], test_name: str, test_before: int, test_after: int) -> dict[str, Any]:
    task_id = "repair_" + uuid4().hex[:12]
    verified = test_before != 0 and test_after == 0
    event = {
        "input": prompt,
        "output": json.dumps({"replacements": replacements}, ensure_ascii=False, sort_keys=True),
        "source": "ailovanta-code-repair",
        "behavior": {"score": 1.0 if verified else 0.0, "test_before": test_before, "test_after": test_after},
        "metadata": {"task_id": task_id, "test_name": test_name, "verified": verified, "created_at": round(time(), 3)},
    }
    return AutoTruthEventStore().add_event(event) if verified else {"accepted": False, "reason": "repair_not_verified", "event": event}
