from __future__ import annotations

from api.storage import SchedulerStore


def main() -> None:
    store = SchedulerStore()
    nodes = [
        {"node_id": "node_route_cpu", "device_name": "route-cpu", "cpu_threads": 8, "memory_gb": 16, "has_gpu": False, "gpu_name": None, "contribution_percent": 30},
        {"node_id": "node_route_gpu", "device_name": "route-gpu", "cpu_threads": 16, "memory_gb": 32, "has_gpu": True, "gpu_name": "demo-gpu", "contribution_percent": 40},
    ]
    jobs = [
        ("job_route_eval", "evaluation", {"priority": 20, "min_cpu_threads": 2}),
        ("job_route_rag", "rag_import", {"priority": 50, "min_memory_gb": 8}),
        ("job_route_lora", "lora_micro", {"priority": 95, "requires_gpu": True, "min_memory_gb": 8}),
    ]
    for node in nodes:
        print("node:", store.register_node(node))
    for job_id, job_type, payload in jobs:
        try:
            print("job:", store.enqueue_job(job_id, job_type, payload))
        except Exception as exc:
            print("skip job", job_id, exc)
    print("cpu preview:", store.queued_route_preview("node_route_cpu"))
    print("gpu preview:", store.queued_route_preview("node_route_gpu"))


if __name__ == "__main__":
    main()
