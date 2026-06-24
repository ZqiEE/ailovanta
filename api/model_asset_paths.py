from __future__ import annotations

from pathlib import Path


def root_dir(root: str = "runtime_data/assets") -> Path:
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def digest_file(digest: str) -> str:
    safe = digest.replace(":", "_").replace("/", "_")
    return safe + ".json"


def digest_path(digest: str, root: str = "runtime_data/assets") -> Path:
    return root_dir(root) / digest_file(digest)
