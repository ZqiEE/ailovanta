# Worker Transport

## Purpose

This is the next step after runtime routing.

```text
owned chat request
-> runtime router selects Ailovanta runtime manifest
-> worker transport calls selected worker
-> worker returns answer
```

## Worker endpoint

A worker must expose:

```text
POST /v1/owned/infer
```

Request fields:

```text
prompt
model_id
version
policy_mode
runtime_id
node_id
model_manifest_hash
```

Response fields:

```text
answer
source
model_id
version
runtime_id
node_id
```

## Configure worker URL

Runtime-specific URL:

```bash
export AILOVANTA_WORKER_URL_RT_OWNED_1=http://127.0.0.1:9001
```

Default URL:

```bash
export AILOVANTA_DEFAULT_WORKER_URL=http://127.0.0.1:9001
```

## Run demo worker

```bash
uvicorn api.demo_worker_app:app --port 9001 --reload
```

## Run owned app

```bash
uvicorn api.main_owned:app --reload
```

## Boundary

Owned runtime no longer returns a placeholder after routing. It now attempts worker inference. If no worker URL is configured or the worker is not reachable, owned chat returns not ready instead of using the bootstrap model.
