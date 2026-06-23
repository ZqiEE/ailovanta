# Ailovanta Technical Overview

## Purpose

Ailovanta is a distributed AI compute network MVP. The public repository focuses on the public shell: local API, node client, dashboard, docs, tests, and safe interface examples.

## Main components

```text
User / developer
  -> FastAPI local runtime
  -> SchedulerStore
  -> Node client
  -> Job runner
  -> Verification engine
  -> Training job planner
  -> Model version registry
  -> Dashboard APIs
```

## Runtime entry points

```text
GET  /
GET  /app
GET  /dashboard
GET  /docs
```

## Job lifecycle

```text
POST /nodes/register
POST /nodes/heartbeat
GET  /jobs/next
POST /jobs/result
GET  /verification/status
GET  /network/status
```

## Training lifecycle

```text
POST /training/jobs
GET  /training/jobs
POST /models/versions
GET  /models/versions
```

## Storage

The public MVP uses SQLite through `SchedulerStore`.

Runtime files are excluded from Git through `.gitignore`:

- `runtime_data/`
- `object_store/`
- `*.sqlite3`
- `*.db`
- `*.log`
- `.env`
- `.env.*`

## Local AI runtime

The public MVP includes an Ollama adapter. If Ollama is unavailable, `/ai/chat` returns a local fallback instead of crashing.

## Public/core split

Public repository:

- Product shell
- Public node client
- Local MVP API
- Demos
- Docs
- Tests
- Safe interfaces

Ailovanta Core:

- H-SwarmTrain Lite modules
- Scheduler / validator / aggregator
- Orchestrator
- Round summaries
- Audit records

## Current limitation

Ailovanta is not yet a production network. It is a local MVP designed to make the architecture runnable, inspectable, and ready for controlled integration with Ailovanta Core.
