from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from api.coding_benchmark_suite import score_unified
from api.coding_factory import CodingFactoryPlanner


@dataclass
class CodingTrainingState:
    base_model: str
    domain_scores: dict[str, float] = field(
        default_factory=lambda: {"frontend": 0.0, "backend": 0.0, "repair": 0.0}
    )
    expert_checkpoints: dict[str, str] = field(default_factory=dict)
    unified_checkpoint: str | None = None
    completed_cycles: int = 0


class CodingAutonomousLoop:
    def __init__(self, planner: CodingFactoryPlanner | None = None) -> None:
        self.planner = planner or CodingFactoryPlanner()

    def next_training_job(
        self,
        state: CodingTrainingState,
        *,
        dataset_uri_by_expert: dict[str, str],
        budget_steps: int = 100,
    ) -> dict[str, Any]:
        cycle = self.planner.plan_autonomous_cycle(
            scores=state.domain_scores,
            base_model=state.base_model,
            dataset_uri_by_expert=dataset_uri_by_expert,
            budget_steps=budget_steps,
        )
        cycle["completed_cycles"] = state.completed_cycles
        return cycle

    def record_expert_result(
        self,
        state: CodingTrainingState,
        *,
        expert: str,
        score: float,
        checkpoint: str,
    ) -> CodingTrainingState:
        if expert not in ("frontend", "backend", "repair"):
            raise ValueError(f"unknown coding expert: {expert}")
        state.domain_scores[expert] = max(0.0, min(1.0, float(score)))
        state.expert_checkpoints[expert] = checkpoint
        state.completed_cycles += 1
        return state

    def can_unify(self, state: CodingTrainingState) -> bool:
        return all(name in state.expert_checkpoints for name in ("frontend", "backend", "repair"))

    def unification_job(self, state: CodingTrainingState, *, budget_steps: int = 100) -> dict[str, Any]:
        if not self.can_unify(state):
            missing = [name for name in ("frontend", "backend", "repair") if name not in state.expert_checkpoints]
            raise ValueError("missing expert checkpoints: " + ", ".join(missing))
        return self.planner.plan_unification_job(
            base_model=state.base_model,
            frontend_checkpoint=state.expert_checkpoints["frontend"],
            backend_checkpoint=state.expert_checkpoints["backend"],
            repair_checkpoint=state.expert_checkpoints["repair"],
            budget_steps=budget_steps,
        )

    def promotion_score(self, state: CodingTrainingState) -> dict[str, Any]:
        return score_unified(
            frontend=state.domain_scores.get("frontend", 0.0),
            backend=state.domain_scores.get("backend", 0.0),
            repair=state.domain_scores.get("repair", 0.0),
        )
