# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Free access attracts users, users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v0.7 Update

v0.7 adds scheduler persistence.

### What changed

- Added `api/storage.py`: SQLite-backed scheduler store
- Updated `api/main.py`: nodes, jobs, and results now persist locally
- Added `docs/SCHEDULER.md`: scheduler persistence guide
- `/network/status` now reports persisted node/job/result counts
- The local node client can keep using the same API, but the scheduler state survives process restarts

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## Current Structure

```text
index.html                    # English-first product MVP
api/main.py                   # FastAPI API using persistent scheduler store
api/storage.py                # SQLite scheduler persistence
api/ollama_adapter.py         # Optional Ollama local AI adapter
api/memory_store.py           # Local JSON memory storage
node_client/client.py         # Hardened local node client
node_client/device.py         # Device and GPU detection
node_client/resource_guard.py # CPU/memory resource guard
node_client/job_runner.py     # Simulated sandboxed job runner
docs/ARCHITECTURE.md          # Architecture notes
docs/ROADMAP.md               # Product roadmap
docs/LOCAL_RUNTIME.md         # Local runtime instructions
docs/OLLAMA.md                # Ollama setup guide
docs/NODE_CLIENT.md           # Node client guide
docs/SCHEDULER.md             # Scheduler persistence guide
validate.py                   # Repository validation
requirements.txt              # Python dependencies
```

## Run Static MVP

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Run Local Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In another terminal:

```bash
python node_client/client.py \
  --api-url http://127.0.0.1:8000 \
  --contribution 30 \
  --max-cpu-percent 70 \
  --min-free-memory-gb 1.5
```

Check persisted scheduler status:

```bash
curl http://127.0.0.1:8000/network/status
```

## Enable Real Local AI

Install Ollama and pull a local model:

```bash
ollama pull qwen2.5:3b
```

The `/ai/chat` endpoint will return `provider: ollama` when Ollama is running, and `provider: fallback` when it is not.

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
