from __future__ import annotations

from api.task_router import TaskRouter
from node_client.coding_inference_worker import run_coding_inference
from node_client.task_policy import TaskPolicy


def test_community_worker_rejects_private_payload_before_inference():
    job = {
        "id": "private-job",
        "type": "coding_inference",
        "payload": {"privacy_scope": "private", "prompt": "secret repository code"},
    }
    try:
        run_coding_inference(job)
    except RuntimeError as exc:
        assert "refuses private" in str(exc)
    else:
        raise AssertionError("private payload must never reach community inference")


def test_task_policy_allows_only_labeled_public_or_synthetic_inference():
    policy = TaskPolicy(allowed_job_types=TaskPolicy.default().allowed_job_types, max_payload_bytes=262144, max_runtime_seconds=600)
    public_job = {"type": "coding_inference", "payload": {"privacy_scope": "public", "prompt": "fix public example"}}
    private_job = {"type": "coding_inference", "payload": {"privacy_scope": "private", "prompt": "secret"}}
    assert policy.validate(public_job)[0] is True
    assert policy.validate(private_job)[0] is False


def test_router_uses_reported_gpu_memory_for_coding_inference():
    router = TaskRouter()
    job = {
        "job_type": "coding_inference",
        "payload": {
            "privacy_scope": "synthetic",
            "requires_gpu": True,
            "min_gpu_memory_gb": 20,
            "min_memory_gb": 16,
        },
    }
    strong = {"node_id": "strong", "has_gpu": True, "gpu_memory_gb": 24, "memory_gb": 64, "cpu_threads": 16}
    weak = {"node_id": "weak", "has_gpu": True, "gpu_memory_gb": 12, "memory_gb": 64, "cpu_threads": 16}
    assert router.can_assign(strong, job)[0] is True
    ok, reason = router.can_assign(weak, job)
    assert ok is False
    assert reason == "not enough gpu memory"
