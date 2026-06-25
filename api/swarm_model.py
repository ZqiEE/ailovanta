from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal
from uuid import uuid4

SwarmStage = Literal["foundation_pretrain", "distillation", "adapter_tune", "evaluation"]
ShardJobType = Literal["foundation_pretrain_shard", "distill_shard", "adapter_train_shard", "eval_shard"]

STAGE_JOB_TYPES: dict[SwarmStage, ShardJobType] = {
    "foundation_pretrain": "foundation_pretrain_shard",
    "distillation": "distill_shard",
    "adapter_tune": "adapter_train_shard",
    "evaluation": "eval_shard",
}


@dataclass(frozen=True)
class DataShard:
    shard_id: str
    dataset_uri: str
    token_start: int
    token_count: int
    content_hash: str
    license_scope: str = "licensed_training"


@dataclass(frozen=True)
class SwarmTrainingPlan:
    plan_id: str
    model_id: str
    base_model: str
    target_version: str
    stage: SwarmStage
    shard_job_type: ShardJobType
    dataset_uri: str
    total_tokens: int
    shard_tokens: int
    max_runtime_seconds: int
    requires_gpu: bool
    min_gpu_memory_gb: float
    policy_mode: str = "open_research"
    shards: list[DataShard] = field(default_factory=list)
    schema_version: str = "ailovanta.swarm_training_plan.v1"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["plan_hash"] = stable_hash(payload)
        return payload


def make_training_plan(
    model_id: str,
    base_model: str,
    target_version: str,
    dataset_uri: str,
    total_tokens: int,
    stage: SwarmStage = "foundation_pretrain",
    shard_tokens: int = 8192,
    max_runtime_seconds: int = 600,
    min_gpu_memory_gb: float = 8.0,
    policy_mode: str = "open_research",
) -> SwarmTrainingPlan:
    if total_tokens <= 0:
        raise ValueError("total_tokens must be positive")
    if shard_tokens <= 0:
        raise ValueError("shard_tokens must be positive")
    plan_id = "swarm_plan_" + uuid4().hex[:12]
    shards: list[DataShard] = []
    for index, token_start in enumerate(range(0, total_tokens, shard_tokens)):
        count = min(shard_tokens, total_tokens - token_start)
        shard_id = f"{plan_id}_shard_{index:05d}"
        shards.append(
            DataShard(
                shard_id=shard_id,
                dataset_uri=dataset_uri,
                token_start=token_start,
                token_count=count,
                content_hash=stable_hash({"dataset_uri": dataset_uri, "token_start": token_start, "token_count": count}),
            )
        )
    return SwarmTrainingPlan(
        plan_id=plan_id,
        model_id=model_id,
        base_model=base_model,
        target_version=target_version,
        stage=stage,
        shard_job_type=STAGE_JOB_TYPES[stage],
        dataset_uri=dataset_uri,
        total_tokens=total_tokens,
        shard_tokens=shard_tokens,
        max_runtime_seconds=max_runtime_seconds,
        requires_gpu=stage in {"foundation_pretrain", "distillation", "adapter_tune"},
        min_gpu_memory_gb=min_gpu_memory_gb,
        policy_mode=policy_mode,
        shards=shards,
    )


def jobs_from_plan(plan: SwarmTrainingPlan) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for shard in plan.shards:
        jobs.append(
            {
                "job_id": shard.shard_id,
                "job_type": plan.shard_job_type,
                "payload": {
                    "schema_version": "ailovanta.swarm_training_job.v1",
                    "plan_id": plan.plan_id,
                    "model_id": plan.model_id,
                    "base_model": plan.base_model,
                    "target_version": plan.target_version,
                    "stage": plan.stage,
                    "policy_mode": plan.policy_mode,
                    "dataset_uri": shard.dataset_uri,
                    "token_start": shard.token_start,
                    "token_count": shard.token_count,
                    "content_hash": shard.content_hash,
                    "requires_gpu": plan.requires_gpu,
                    "min_gpu_memory_gb": plan.min_gpu_memory_gb,
                    "max_runtime_seconds": plan.max_runtime_seconds,
                    "expected_output": "checkpoint_delta",
                },
            }
        )
    return jobs


def make_checkpoint_delta(job: dict[str, Any], node_id: str, train_loss: float | None = None, eval_loss: float | None = None) -> dict[str, Any]:
    payload = job.get("payload", {})
    raw = {
        "job_id": job.get("id") or job.get("job_id"),
        "node_id": node_id,
        "plan_id": payload.get("plan_id"),
        "stage": payload.get("stage"),
        "model_id": payload.get("model_id"),
        "target_version": payload.get("target_version"),
        "token_start": payload.get("token_start"),
        "token_count": payload.get("token_count"),
        "content_hash": payload.get("content_hash"),
        "train_loss": train_loss,
        "eval_loss": eval_loss,
    }
    return {
        "schema_version": "ailovanta.checkpoint_delta.v1",
        **raw,
        "delta_hash": stable_hash(raw),
        "delta_ref": "delta://" + stable_hash(raw).removeprefix("sha256:"),
    }


def aggregate_deltas(plan: dict[str, Any], deltas: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [delta for delta in deltas if delta.get("delta_hash")]
    aggregate = {
        "schema_version": "ailovanta.swarm_checkpoint_set.v1",
        "plan_id": plan["plan_id"],
        "model_id": plan["model_id"],
        "base_model": plan["base_model"],
        "target_version": plan["target_version"],
        "stage": plan["stage"],
        "accepted_delta_count": len(accepted),
        "expected_shard_count": len(plan.get("shards", [])),
        "delta_hashes": sorted(delta["delta_hash"] for delta in accepted),
    }
    aggregate["checkpoint_set_hash"] = stable_hash(aggregate)
    aggregate["ready_for_eval"] = aggregate["accepted_delta_count"] > 0 and aggregate["accepted_delta_count"] == aggregate["expected_shard_count"]
    return aggregate


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()
