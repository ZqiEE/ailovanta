from __future__ import annotations

import re
from typing import Any

from api.project_store import ProjectStore


TOKEN_RE = re.compile(r"[A-Za-z0-9_./-]{3,}")
CORE_FILES = {
    "readme.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "cargo.toml",
    "go.mod",
    "dockerfile",
    "docker-compose.yml",
    "tsconfig.json",
    "vite.config.ts",
    "next.config.js",
}


def select_project_context(
    store: ProjectStore,
    project_id: str,
    task: str,
    *,
    focused_file: str | None = None,
    max_chars: int = 120000,
) -> dict[str, Any]:
    tokens = {token.lower() for token in TOKEN_RE.findall(task) if len(token) >= 3}
    rows: list[dict[str, Any]] = []
    for item in store.list_files(project_id):
        path = item["path"]
        content = store.read_file(project_id, path)["content"]
        lower_path = path.lower()
        lower_content = content.lower()
        score = 0.0
        if focused_file and path == focused_file:
            score += 1000.0
        if lower_path.rsplit("/", 1)[-1] in CORE_FILES:
            score += 30.0
        for token in tokens:
            if token in lower_path:
                score += 12.0
            count = lower_content.count(token)
            score += min(count, 8) * 1.5
        if "/test" in lower_path or lower_path.startswith("test") or "/tests/" in lower_path:
            if any(word in tokens for word in {"bug", "fix", "repair", "test", "error", "fail"}):
                score += 15.0
        rows.append({"path": path, "content": content, "score": score})

    rows.sort(key=lambda row: (row["score"], -len(row["content"])), reverse=True)
    selected: list[dict[str, Any]] = []
    remaining = max_chars
    for row in rows:
        block = f"\n--- FILE: {row['path']} ---\n{row['content']}\n--- END FILE ---\n"
        if len(block) > remaining:
            if not selected:
                block = block[:remaining]
            else:
                continue
        selected.append({"path": row["path"], "score": round(float(row["score"]), 2), "block": block})
        remaining -= len(block)
        if remaining <= 0:
            break

    return {
        "context": "".join(row["block"] for row in selected),
        "selected_files": [row["path"] for row in selected],
        "scores": {row["path"]: row["score"] for row in selected},
        "total_files": len(rows),
    }
