from api.coding_autonomous_loop import CodingAutonomousLoop, CodingTrainingState
from api.coding_benchmark_suite import score_domain, score_unified
from api.coding_factory import CodingFactoryPlanner


def test_three_experts_have_distinct_jobs():
    planner = CodingFactoryPlanner()
    jobs = {
        expert: planner.plan_expert_job(
            expert,
            base_model="base-model",
            dataset_uri=f"dataset://{expert}",
        )
        for expert in ("frontend", "backend", "repair")
    }
    assert jobs["frontend"]["job_type"] == "coding_frontend_rl"
    assert jobs["backend"]["job_type"] == "coding_backend_rl"
    assert jobs["repair"]["job_type"] == "coding_repair_rl"


def test_autonomous_cycle_targets_weakest_domain():
    planner = CodingFactoryPlanner()
    cycle = planner.plan_autonomous_cycle(
        scores={"frontend": 0.82, "backend": 0.76, "repair": 0.61},
        base_model="base-model",
        dataset_uri_by_expert={
            "frontend": "dataset://frontend",
            "backend": "dataset://backend",
            "repair": "dataset://repair",
        },
    )
    assert cycle["selected_expert"] == "repair"


def test_unified_score_requires_domain_floor():
    result = score_unified(frontend=0.95, backend=0.94, repair=0.40)
    assert result["passed"] is False
    assert result["weakest_domain"] == "repair"


def test_frontend_scorecard_is_weighted():
    result = score_domain(
        "frontend",
        {
            "browser_render": True,
            "visual_quality": 0.9,
            "interaction_success": 0.9,
            "responsive_quality": 0.8,
            "accessibility": 0.8,
        },
    )
    assert result["score"] > 0.8


def test_autonomous_loop_can_unify_after_all_experts_exist():
    loop = CodingAutonomousLoop()
    state = CodingTrainingState(base_model="base-model")
    loop.record_expert_result(state, expert="frontend", score=0.81, checkpoint="ckpt-front")
    loop.record_expert_result(state, expert="backend", score=0.82, checkpoint="ckpt-back")
    loop.record_expert_result(state, expert="repair", score=0.83, checkpoint="ckpt-repair")
    assert loop.can_unify(state)
    job = loop.unification_job(state)
    assert job["job_type"] == "coding_unify"
