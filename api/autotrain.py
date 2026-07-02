from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from api.autotruth_store import AutoTruthEventStore
from api.learning_gate import run_guarded_learning_pipeline


class AutoTrainError(ValueError):
    pass


def _stable_hash(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def event_to_sft_row(event: dict[str, Any]) -> dict[str, Any]:
    instruction = str(event.get("input") or "").strip()
    output = str(event.get("output") or "").strip()
    if not instruction or not output:
        raise AutoTrainError("event is missing input or output")
    behavior = dict(event.get("behavior") or {})
    score = float(behavior.get("score", behavior.get("quality", 1.0)) or 1.0)
    return {
        "instruction": instruction,
        "output": output,
        "score": max(0.0, min(1.0, score)),
        "sample_id": event.get("event_id"),
        "source": event.get("source") or "public-runtime",
    }


def build_pack_from_events(events: list[dict[str, Any]], model_id: str = "ailovanta-owned", target_version: str = "candidate") -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for event in events:
        try:
            rows.append(event_to_sft_row(event))
        except AutoTrainError:
            continue
    if not rows:
        raise AutoTrainError("no usable learning events for autotrain")

    digest = _stable_hash(rows)
    return {
        "schema_version": "ailovanta.autotrain.pack.v1",
        "pack_id": "autotrain_pack_" + digest[:12],
        "pack_hash": "sha256:" + digest,
        "model_id": model_id,
        "target_version": target_version,
        "sft": rows,
        "dpo": [],
        "metadata": {
            "source": "autotrain_events",
            "event_count": len(events),
            "usable_rows": len(rows),
            "created_at": round(time(), 3),
        },
    }


def ensure_autotrain_pack(
    store: AutoTruthEventStore | None = None,
    *,
    min_events: int = 1,
    event_limit: int = 1000,
    model_id: str = "ailovanta-owned",
    target_version: str = "candidate",
    reuse_latest_pack: bool = True,
) -> dict[str, Any]:
    event_store = store or AutoTruthEventStore()
    if reuse_latest_pack:
        latest = event_store.latest_pack()
        if latest:
            return {"created": False, "pack": latest, "reason": "latest_pack_reused"}

    events = list(reversed(event_store.list_events(limit=event_limit)))
    if len(events) < min_events:
        raise AutoTrainError(f"not enough learning events: {len(events)} < {min_events}")

    pack = build_pack_from_events(events, model_id=model_id, target_version=target_version)
    imported = event_store.import_run(
        {
            "run_id": "autotrain_run_" + pack["pack_hash"].removeprefix("sha256:")[:12],
            "rows": pack["sft"],
            "training_pack": pack,
            "metadata": {"source": "autotrain.ensure_pack"},
        }
    )
    return {"created": True, "pack": pack, "imported": imported, "reason": "events_packed"}


def run_autotrain(
    *,
    core_path: str | Path | None = None,
    work_dir: str | Path = "runtime_data/autotrain_pipeline",
    min_events: int = 1,
    event_limit: int = 1000,
    reuse_latest_pack: bool = True,
    baseline_model: str = "ailovanta-owned:baseline",
    baseline_score: float = 0.45,
    allow_shadow_import: bool = False,
    execute_checkpoints: bool = False,
    checkpoint_output_root: str | Path | None = None,
    training_command: str | None = None,
    model_backend: str | None = None,
    base_model: str | None = None,
    backend_output_dir: str | Path | None = None,
    backend_device: str | None = None,
    backend_max_steps: int | None = None,
    backend_lr: float | None = None,
    prepare_runtime: bool = True,
    runtime_id: str = "rt-owned-1",
    node_id: str = "learning_node_1",
    gpu_memory_gb: float = 24.0,
    model_id: str = "ailovanta-owned",
    target_version: str = "candidate",
    max_steps: int = 100,
) -> dict[str, Any]:
    pack_result = ensure_autotrain_pack(
        min_events=min_events,
        event_limit=event_limit,
        model_id=model_id,
        target_version=target_version,
        reuse_latest_pack=reuse_latest_pack,
    )
    pipeline = run_guarded_learning_pipeline(
        core_path=core_path,
        work_dir=work_dir,
        baseline_model=baseline_model,
        baseline_score=baseline_score,
        allow_shadow_import=allow_shadow_import,
        execute_checkpoints=execute_checkpoints,
        checkpoint_output_root=checkpoint_output_root,
        training_command=training_command,
        model_backend=model_backend,
        base_model=base_model,
        backend_output_dir=backend_output_dir,
        backend_device=backend_device,
        backend_max_steps=backend_max_steps,
        backend_lr=backend_lr,
        prepare_runtime=prepare_runtime,
        runtime_id=runtime_id,
        node_id=node_id,
        runtime_gpu_memory_gb=gpu_memory_gb,
        model_id=model_id,
        target_version=target_version,
        node_id=node_id,
        gpu_memory_gb=gpu_memory_gb,
        max_steps=max_steps,
    )
    return {
        "ok": True,
        "stage": "autotrain_complete",
        "pack": pack_result,
        "pipeline": pipeline,
        "runtime_updated": bool(pipeline.get("runtime_updated")),
    }
