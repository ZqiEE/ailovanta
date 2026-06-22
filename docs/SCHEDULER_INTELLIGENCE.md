# Scheduler Intelligence

v1.6 adds capability-aware routing.

## What changed

- Jobs can declare priority
- Jobs can require GPU
- Jobs can require minimum memory
- Jobs can require minimum CPU threads
- CPU nodes skip GPU-only jobs
- GPU nodes can receive GPU jobs
- Route preview explains matching decisions

## Job payload fields

```json
{
  "priority": 90,
  "requires_gpu": true,
  "min_memory_gb": 8,
  "min_cpu_threads": 4
}
```

## Scripts

```bash
python scripts/seed_routing_demo.py
python scripts/route_preview.py --node-id node_route_gpu
```

## Tests

```bash
python -m pytest tests/test_task_router.py tests/test_scheduler_routing.py -q
```
