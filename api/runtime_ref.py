from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

SCHEMA = "ailovanta.runtime_ref.v1"


def to_local_path(value: str) -> Path | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "file":
        return _file_uri_to_path(value, parsed)
    if parsed.scheme == "":
        return Path(value)
    return None


def _file_uri_to_path(value: str, parsed) -> Path:
    # POSIX URI: file:///tmp/checkpoint.bin -> /tmp/checkpoint.bin
    if parsed.path and parsed.path not in {"/", ""}:
        path = unquote(parsed.path)
        # Windows URI produced by Path.as_uri(): file:///C:/tmp/a.bin
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return Path(path)

    # Windows string often produced in tests/user config:
    # file://C:\Users\... or file://C:/Users/...
    raw = value.removeprefix("file://")
    if raw:
        return Path(unquote(raw))

    if parsed.netloc:
        return Path(unquote(parsed.netloc))
    return Path("")


def check_runtime_ref(item: dict[str, Any]) -> dict[str, Any]:
    ref = str(item.get("backend_ref") or item.get("checkpoint_uri") or "")
    path = to_local_path(ref)
    if path is None:
        return make_result(item, False, "unsupported_ref", ref=ref)
    if not path.exists():
        return make_result(item, False, "missing_path", ref=ref, path=str(path))
    kind = "directory" if path.is_dir() else "file"
    return make_result(item, True, "path_ready", ref=ref, path=str(path), kind=kind)


def make_result(item: dict[str, Any], ready: bool, reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "ready": ready,
        "reason": reason,
        "binding_id": item.get("binding_id"),
        "model_key": item.get("model_key"),
        "backend_kind": item.get("backend_kind"),
        **extra,
    }
