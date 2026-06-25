from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Task:
    task_id: str
    plan_id: str
    node_id: str
    input_uri: str
    output_uri: str
    max_steps: int
    token_budget: int
    schema_version: str = "ailovanta.worker_task.v1"
    created_at: float = field(default_factory=lambda: round(time(), 3))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Result:
    task_id: str
    node_id: str
    checkpoint_uri: str
    checkpoint_hash: str
    token_count: int
    train_loss: float
    eval_loss: float
    schema_version: str = "ailovanta.worker_result.v1"
    result_id: str = field(default_factory=lambda: "result_" + uuid4().hex[:12])
    created_at: float = field(default_factory=lambda: round(time(), 3))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_task(plan: dict[str, Any], node_id: str, input_uri: str, output_uri: str) -> dict[str, Any]:
    return Task("task_" + uuid4().hex[:12], str(plan.get("plan_id")), node_id, input_uri, output_uri, int(plan.get("max_steps") or 1), int(plan.get("estimated_total_tokens") or 0)).to_dict()


def make_result(payload: dict[str, Any]) -> dict[str, Any]:
    return Result(str(payload["task_id"]), str(payload["node_id"]), str(payload["checkpoint_uri"]), str(payload["checkpoint_hash"]), int(payload.get("token_count") or 0), float(payload.get("train_loss") or 0.0), float(payload.get("eval_loss") or 0.0)).to_dict()
