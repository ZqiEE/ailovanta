# Owned Runtime Production Path

This document describes the real Ailovanta-owned runtime path. It is not the demo path.

## Required services

1. Ailovanta API
2. Ailovanta worker
3. Local or hosted model runtime loaded with the Ailovanta model artifact
4. Registered runtime model manifest
5. Registered trusted runtime node

## Environment

```bash
cp .env.example .env
```

Important values:

```text
OLLAMA_MODEL=ailovanta-owned:candidate
AILOVANTA_DEFAULT_WORKER_URL=http://127.0.0.1:9001
```

## One command

```bash
python scripts/run_owned_stack.py
```

This starts API and worker, registers model and node, checks readiness, then calls owned-chat.

Keep services running:

```bash
AILOVANTA_KEEP_SERVICES_RUNNING=true python scripts/run_owned_stack.py
```

## Manual path

```bash
uvicorn api.main_owned:app --reload
uvicorn api.worker:app --port 9001 --reload
python scripts/register_owned_runtime.py
python scripts/check_owned_runtime_ready.py
python scripts/call_owned_chat.py
```

The call must return:

```text
owned_model_ready: true
source: ailovanta-worker-local-runtime or ailovanta-worker-backend
```

## Real production rule

The worker must return a response from a configured model runtime, not fixed text. The runtime manifest hash must come from the promoted core artifact hash or a stable sha256 manifest hash.

## Current status

The repository now supports this path:

```text
core result
-> artifact hash
-> runtime model manifest
-> trusted runtime node
-> owned chat
-> worker inference
```

The remaining external requirement is an actual model runtime process with the Ailovanta artifact loaded.
