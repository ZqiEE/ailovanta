from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from time import time
from typing import Any


DEFAULT_PATHS = [
    "runtime_data/catalog.json",
    "runtime_data/runtime.sqlite3",
    "runtime_data/route_book.sqlite3",
    "runtime_data/node_trust.sqlite3",
    "runtime_data/artifact_bindings.sqlite3",
    "runtime_data/manifests",
    "runtime_data/anchors",
    "runtime_data/artifact_manifests",
]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def safe_name(value: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)
    return out.strip("._") or "snapshot"


class BackupStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv("AILOVANTA_BACKUP_PATH", "runtime_data/backups"))
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, label: str = "manual", paths: list[str] | None = None) -> dict[str, Any]:
        snapshot_id = safe_name(label) + "_" + str(int(time()))
        target = self.root / snapshot_id
        target.mkdir(parents=True, exist_ok=False)
        manifest: dict[str, Any] = {
            "schema_version": "ailovanta.backup_snapshot.v1",
            "snapshot_id": snapshot_id,
            "created_at": round(time(), 3),
            "source_paths": [],
            "files": [],
            "missing": [],
        }
        for raw in paths or DEFAULT_PATHS:
            src = Path(raw)
            if not src.exists():
                manifest["missing"].append(raw)
                continue
            if src.is_dir():
                for file in sorted(src.rglob("*")):
                    if file.is_file():
                        self._copy_file(file, target, manifest)
            else:
                self._copy_file(src, target, manifest)
            manifest["source_paths"].append(raw)
        manifest["file_count"] = len(manifest["files"])
        manifest["manifest_hash"] = self._manifest_hash(manifest)
        (target / "backup_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    def list(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*/backup_manifest.json"), reverse=True):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                items.append({"snapshot_id": path.parent.name, "ok": False, "reason": "manifest_read_error"})
        return items

    def verify(self, snapshot_id: str) -> dict[str, Any]:
        manifest_path = self.root / safe_name(snapshot_id) / "backup_manifest.json"
        if not manifest_path.exists():
            return {"ok": False, "reason": "snapshot_not_found", "snapshot_id": snapshot_id}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        blockers: list[str] = []
        for item in manifest.get("files", []):
            path = self.root / safe_name(snapshot_id) / item["backup_path"]
            if not path.exists():
                blockers.append("missing_backup_file:" + item["source_path"])
                continue
            digest = sha256_file(path)
            if digest != item.get("sha256"):
                blockers.append("hash_mismatch:" + item["source_path"])
        expected = manifest.get("manifest_hash")
        actual = self._manifest_hash(manifest)
        if expected and expected != actual:
            blockers.append("manifest_hash_mismatch")
        return {"ok": not blockers, "snapshot_id": snapshot_id, "blockers": sorted(set(blockers)), "file_count": len(manifest.get("files", []))}

    def restore(self, snapshot_id: str, dry_run: bool = True) -> dict[str, Any]:
        verified = self.verify(snapshot_id)
        if not verified.get("ok"):
            return {"ok": False, "reason": "snapshot_verify_failed", "verify": verified}
        root = self.root / safe_name(snapshot_id)
        manifest = json.loads((root / "backup_manifest.json").read_text(encoding="utf-8"))
        restored: list[str] = []
        for item in manifest.get("files", []):
            src = root / item["backup_path"]
            dest = Path(item["source_path"])
            restored.append(str(dest))
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        return {"ok": True, "snapshot_id": snapshot_id, "dry_run": dry_run, "restored": restored, "verify": verified}

    def latest_status(self) -> dict[str, Any]:
        items = self.list()
        if not items:
            return {"ok": False, "reason": "no_backup_snapshots"}
        latest = items[0]
        verify = self.verify(latest["snapshot_id"])
        return {"ok": bool(verify.get("ok")), "latest": latest, "verify": verify}

    def _copy_file(self, src: Path, target: Path, manifest: dict[str, Any]) -> None:
        backup_path = Path("files") / safe_name(str(src))
        dest = target / backup_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        manifest["files"].append({"source_path": str(src), "backup_path": str(backup_path), "sha256": sha256_file(dest), "size_bytes": dest.stat().st_size})

    @staticmethod
    def _manifest_hash(manifest: dict[str, Any]) -> str:
        body = {key: value for key, value in manifest.items() if key != "manifest_hash"}
        raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()
