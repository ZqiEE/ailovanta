from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from api.prod_config import load_config


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class StoredArtifact:
    artifact_uri: str
    artifact_hash: str
    store: str
    size_bytes: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_uri": self.artifact_uri,
            "artifact_hash": self.artifact_hash,
            "store": self.store,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }


class ArtifactStore(Protocol):
    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        ...


class LocalArtifactStore:
    def __init__(self, root: str | Path = "runtime_data/artifacts") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        safe_id = artifact_id.replace("/", "_").replace(":", "_")
        target_dir = self.root / safe_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        digest = file_sha256(target)
        meta = {"source_path": str(source), **(metadata or {})}
        (target_dir / "metadata.json").write_text(json.dumps({"artifact_hash": digest, "artifact_uri": str(target), "metadata": meta}, ensure_ascii=False, indent=2), encoding="utf-8")
        return StoredArtifact(artifact_uri=str(target), artifact_hash=digest, store="local", size_bytes=target.stat().st_size, metadata=meta)


class ExternalArtifactStore:
    def __init__(self, uri: str | None) -> None:
        self.uri = uri

    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        raise NotImplementedError("external artifact storage adapter is configured but not implemented in local scaffold")


def get_artifact_store() -> ArtifactStore:
    cfg = load_config()
    if cfg.artifact_store == "local":
        return LocalArtifactStore(cfg.artifact_store_uri or "runtime_data/artifacts")
    return ExternalArtifactStore(cfg.artifact_store_uri)
