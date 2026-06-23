# Ailovanta Project Status

## Current stage

Ailovanta is a local MVP and public shell for a distributed AI compute network.

It is not yet a public production network, not yet a real global training network, and not yet a replacement for mature cloud GPU infrastructure.

## Done in the public repository

- Public landing page served at `/app`
- Local dashboard served at `/dashboard`
- FastAPI local runtime
- Node registration
- Node heartbeat
- Job queue
- Job assignment
- Result submission
- Lightweight verification records
- Trust updates after results
- Failed-job retry endpoint
- Stale-job requeue endpoint
- Training job records
- Model version registry
- Ollama adapter with fallback
- Local memory endpoints
- Local node client
- Docker / Compose
- Validation script
- Pytest coverage for core API flow

## Done in Ailovanta Core

- H-SwarmTrain algorithm notes
- Lite training scheduler
- Machine profile normalization
- Task assignment records
- Worker registry contract
- Demo worker
- Orchestrator
- Validation and aggregation modules
- Round summaries
- SQLite summary store
- Run audit log

## Not done yet

- Production authentication
- Public node admission
- Strong job signing
- Strong task sandboxing
- Real GPU worker runtime
- Real LoRA/QLoRA training execution
- Real distributed model artifact storage
- Public reward settlement
- PostgreSQL backend
- Redis-style queue locking
- Hosted production gateway
- Public testnet

## Safe public claim

Use this:

```text
Ailovanta is building a distributed AI compute network. The current release is a local MVP with node registration, job dispatch, verification, training job records, and a public/private architecture boundary.
```

Avoid this:

```text
Ailovanta has already solved global distributed AI training.
```

## Next best engineering step

The next best step is to connect the public job lifecycle to Ailovanta Core's H-SwarmTrain Lite orchestration through a stable interface, while keeping production coordination logic outside the public repository.
