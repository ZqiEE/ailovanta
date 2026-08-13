from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal
from uuid import uuid4


CodingExpert = Literal["frontend", "backend", "repair"]
CodingJobKind = Literal[
    "coding_frontend_rl",
    "coding_backend_rl",
    "coding_repair_rl",
    "coding_unify",
    "coding_eval",
]


@dataclass(frozen=True)
class ExpertSpec:
    name: CodingExpert
    objective: str
    teacher_profile: str
    verifier_signals: tuple[str, ...]
    preferred_worker_capabilities: tuple[str, ...]


EXPERT_SPECS: dict[CodingExpert, ExpertSpec] = {
    "frontend": ExpertSpec(
        name="frontend",
        objective="Generate visually strong, responsive and interaction-correct user interfaces from product intent, screenshots and design references.",
        teacher_profile="gemini_like_frontend",
        verifier_signals=(
            "browser_render",
            "visual_similarity",
            "layout_quality",
            "interaction_success",
            "responsive_checks",
            "accessibility_checks",
        ),
        preferred_worker_capabilities=("gpu", "browser", "vision", "sandbox"),
    ),
    "backend": ExpertSpec(
        name="backend",
        objective="Implement reliable repository-level features across APIs, databases, services and infrastructure with long-horizon engineering discipline.",
        teacher_profile="claude_code_like_backend",
        verifier_signals=(
            "build_success",
            "unit_tests",
            "integration_tests",
            "typecheck",
            "api_contracts",
            "database_checks",
        ),
        preferred_worker_capabilities=("gpu", "cpu", "docker", "sandbox"),
    ),
    "repair": ExpertSpec(
        name="repair",
        objective="Reproduce, localize and repair software defects with minimal regressions and strong verification.",
        teacher_profile="codex_like_repair",
        verifier_signals=(
            "bug_reproduced",
            "root_cause_localized",
            "failing_test_fixed",
            "regression_suite",
            "patch_minimality",
        ),
        preferred_worker_capabilities=("gpu", "cpu", "docker", "sandbox"),
    ),
}


class CodingFactoryError(ValueError):
    pass


class CodingFactoryPlanner:
    """Builds scheduler-ready jobs for the three-expert training factory.

    This module intentionally does not perform model training itself. It turns a
    model-improvement objective into jobs that the existing Ailovanta scheduler,
    distributed workers and validators can execute.
    """

    def expert_spec(self, expert: CodingExpert) -> dict[str, Any]:
        try:
            return asdict(EXPERT_SPECS[expert])
        except KeyError as exc:
            raise CodingFactoryError(f"unknown coding expert: {expert}") from exc

    def plan_expert_job(
        self,
        expert: CodingExpert,
        *,
        base_model: str,
        dataset_uri: str,
        budget_steps: int = 100,
        round_id: str | None = None,
        autonomous: bool = True,
    ) -> dict[str, Any]:
        if budget_steps < 1:
            raise CodingFactoryError("budget_steps must be positive")
        spec = EXPERT_SPECS[expert]
        job_type: CodingJobKind = {
            "frontend": "coding_frontend_rl",
            "backend": "coding_backend_rl",
            "repair": "coding_repair_rl",
        }[expert]
        return {
            "job_id": "code_" + uuid4().hex[:12],
            "job_type": job_type,
            "payload": {
                "schema_version": "ailovanta.coding.expert-job.v1",
                "expert": expert,
                "objective": spec.objective,
                "teacher_profile": spec.teacher_profile,
                "verifier_signals": list(spec.verifier_signals),
                "preferred_worker_capabilities": list(spec.preferred_worker_capabilities),
                "base_model": base_model,
                "dataset_uri": dataset_uri,
                "budget_steps": budget_steps,
                "round_id": round_id or "round_" + uuid4().hex[:10],
                "autonomous": autonomous,
            },
        }

    def plan_unification_job(
        self,
        *,
        base_model: str,
        frontend_checkpoint: str,
        backend_checkpoint: str,
        repair_checkpoint: str,
        method: str = "multi_teacher_on_policy_distillation",
        budget_steps: int = 100,
    ) -> dict[str, Any]:
        return {
            "job_id": "unify_" + uuid4().hex[:12],
            "job_type": "coding_unify",
            "payload": {
                "schema_version": "ailovanta.coding.unify-job.v1",
                "base_model": base_model,
                "experts": {
                    "frontend": frontend_checkpoint,
                    "backend": backend_checkpoint,
                    "repair": repair_checkpoint,
                },
                "method": method,
                "budget_steps": budget_steps,
                "promotion_requires_all_domains": True,
            },
        }

    def choose_next_expert(self, scores: dict[str, float]) -> CodingExpert:
        """Select the weakest expert for the next autonomous training cycle."""
        normalized: dict[CodingExpert, float] = {}
        for expert in EXPERT_SPECS:
            value = float(scores.get(expert, 0.0))
            normalized[expert] = max(0.0, min(1.0, value))
        return min(normalized, key=normalized.get)

    def plan_autonomous_cycle(
        self,
        *,
        scores: dict[str, float],
        base_model: str,
        dataset_uri_by_expert: dict[str, str],
        budget_steps: int = 100,
    ) -> dict[str, Any]:
        expert = self.choose_next_expert(scores)
        dataset_uri = dataset_uri_by_expert.get(expert)
        if not dataset_uri:
            raise CodingFactoryError(f"missing dataset URI for {expert}")
        job = self.plan_expert_job(
            expert,
            base_model=base_model,
            dataset_uri=dataset_uri,
            budget_steps=budget_steps,
            autonomous=True,
        )
        return {
            "stage": "coding_autonomous_cycle_planned",
            "selected_expert": expert,
            "scores": {name: float(scores.get(name, 0.0)) for name in EXPERT_SPECS},
            "job": job,
        }
