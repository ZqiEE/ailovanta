from __future__ import annotations

import ast
import json
import tomllib
from html.parser import HTMLParser
from typing import Any

from api.project_store import ProjectStore


class _HTMLCheck(HTMLParser):
    pass


def validate_project(store: ProjectStore, project_id: str) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    checked = 0
    for item in store.list_files(project_id):
        path = item["path"]
        content = store.read_file(project_id, path)["content"]
        suffix = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
        try:
            if suffix == ".py":
                ast.parse(content, filename=path)
            elif suffix == ".json":
                json.loads(content)
            elif suffix == ".toml":
                tomllib.loads(content)
            elif suffix in {".html", ".htm"}:
                parser = _HTMLCheck()
                parser.feed(content)
                parser.close()
            elif suffix in {".yaml", ".yml"}:
                import yaml

                yaml.safe_load(content)
            else:
                continue
            checked += 1
        except Exception as exc:
            diagnostics.append({
                "path": path,
                "kind": "syntax",
                "message": str(exc)[:500],
            })
    return {
        "ok": not diagnostics,
        "checked_files": checked,
        "diagnostics": diagnostics,
    }
