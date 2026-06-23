# Ailovanta API Reference

Base URL for local runtime:

```text
http://127.0.0.1:8000
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Health and status

```text
GET /
GET /health
GET /ready
GET /network/status
GET /verification/status
GET /dashboard/summary
```

Example:

```bash
curl http://127.0.0.1:8000/network/status
```

## Nodes

```text
POST /nodes/register
POST /nodes/heartbeat
GET  /nodes
```

Register a node:

```bash
curl -X POST http://127.0.0.1:8000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "local-node",
    "cpu_threads": 4,
    "memory_gb": 8,
    "has_gpu": false,
    "gpu_name": null,
    "contribution_percent": 30
  }'
```

Send heartbeat:

```bash
curl -X POST http://127.0.0.1:8000/nodes/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"node_id":"node_xxx","status":"online"}'
```

## Jobs

```text
GET  /jobs
GET  /jobs/next
POST /jobs/result
POST /jobs/retry-failed
POST /jobs/requeue-stale
```

Fetch a job:

```bash
curl "http://127.0.0.1:8000/jobs/next?node_id=node_xxx"
```

Submit a result:

```bash
curl -X POST http://127.0.0.1:8000/jobs/result \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node_xxx",
    "job_id": "job-rag-001",
    "status": "ok",
    "output_summary": "simulated local result"
  }'
```

## Local AI and memory

```text
POST /ai/chat
GET  /memory
POST /memory
DELETE /memory
GET  /usage/summary
```

Chat request:

```bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Ailovanta in one sentence.",
    "mode": "open",
    "user_id": "local",
    "remember": false
  }'
```

If Ollama is not running, the API returns a safe local fallback response instead of crashing.

## Training

```text
POST /training/jobs
GET  /training/jobs
POST /models/versions
GET  /models/versions
```

Create a training job:

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "rag_import",
    "name": "demo-rag",
    "dataset_uri": "file://demo/docs",
    "base_model": "qwen2.5:3b",
    "max_steps": 100,
    "notes": "local demo"
  }'
```

Register a model version:

```bash
curl -X POST http://127.0.0.1:8000/models/versions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-model",
    "base_model": "qwen2.5:3b",
    "source_job_id": "train_xxx",
    "notes": "local demo model version"
  }'
```

## Minimal flow

1. Register node
2. Fetch next job
3. Submit result
4. Check verification status
5. Create training job
6. Register model version
7. Read dashboard summary

## Smoke test

Start the API first:

```bash
uvicorn api.main:app --reload
```

Then run:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```
