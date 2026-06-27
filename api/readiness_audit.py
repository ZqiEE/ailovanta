from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.catalog import Catalog
from api.prod_config import load_config
from api.receipt_gate import ready_for_catalog_publish


class ReadinessAudit:
    def __init__(self, catalog: Catalog | None = None) -> None:
        self.catalog = catalog or Catalog()

    def check_item(self, item: dict[str, Any]) -> dict[str, Any]:
        gate = ready_for_catalog_publish(item)
        blockers: list[str] = []
        warnings: list[str] = []
        uri = str(item.get("artifact_uri") or item.get("location") or "")
        digest = str(item.get("artifact_hash") or item.get("digest") or "")
        if not uri:
            blockers.append("missing_artifact_uri")
        if uri and not uri.startswith(("s3://", "ipfs://", "file://", "http://", "https://")):
            blockers.append("artifact_uri_not_portable")
        if uri.startswith("file://"):
            warnings.append("local_file_artifact")
        if not digest.startswith("sha256:"):
            blockers.append("artifact_hash_not_sha256")
        if not gate.get("ok"):
            blockers.append("publish_gate:" + str(gate.get("reason")))
        return {"item_id": item.get("id"), "name": item.get("name"), "version": item.get("version"), "status": item.get("status"), "ok": not blockers, "blockers": blockers, "warnings": warnings, "gate": gate, "artifact_uri": uri, "artifact_hash": digest}

    def check_catalog(self, status: str | None = "published") -> dict[str, Any]:
        items = self.catalog.list(status=status)
        checked = [self.check_item(item) for item in items]
        blockers = [item for item in checked if not item["ok"]]
        return {"ok": not blockers, "status": status, "count": len(checked), "blockers": blockers, "items": checked}

    def check_manifests(self, manifest_dir: str | Path = "runtime_data/manifests") -> dict[str, Any]:
        root = Path(manifest_dir)
        if not root.exists():
            return {"ok": True, "count": 0, "items": []}
        checked: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        for path in sorted(root.glob("*.json")):
            item_blockers: list[str] = []
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                manifest = {}
                item_blockers.append("manifest_json_error:" + exc.__class__.__name__)
            digest = str(manifest.get("artifact_hash") or manifest.get("digest") or "")
            if manifest and not digest.startswith("sha256:"):
                item_blockers.append("manifest_missing_sha256_hash")
            if manifest and not manifest.get("proof"):
                item_blockers.append("manifest_missing_proof")
            route = manifest.get("route") if isinstance(manifest.get("route"), dict) else {}
            if manifest and not manifest.get("anchor_receipt") and not route.get("receipt"):
                item_blockers.append("manifest_missing_anchor_receipt")
            item = {"path": str(path), "ok": not item_blockers, "blockers": item_blockers, "name": manifest.get("name"), "version": manifest.get("version")}
            checked.append(item)
            if item_blockers:
                blockers.append(item)
        return {"ok": not blockers, "count": len(checked), "blockers": blockers, "items": checked}

    def production_check(self) -> dict[str, Any]:
        cfg = load_config()
        blockers: list[str] = []
        warnings: list[str] = []
        if cfg.env != "local" and cfg.artifact_store == "local":
            blockers.append("production_artifact_store_is_local")
        if cfg.env != "local" and cfg.chain_anchor == "file":
            blockers.append("production_anchor_is_file")
        if cfg.env == "local":
            warnings.append("local_environment")
        catalog = self.check_catalog(status="published")
        manifests = self.check_manifests()
        if not catalog.get("ok"):
            blockers.append("catalog_readiness_failed")
        if not manifests.get("ok"):
            blockers.append("manifest_readiness_failed")
        return {"ok": not blockers, "blockers": blockers, "warnings": warnings, "catalog": catalog, "manifests": manifests}
