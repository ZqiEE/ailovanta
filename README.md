# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Free access attracts users, users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v0.6 Update

v0.6 hardens the local node client.

### What changed

- Added `node_client/device.py`: CPU, memory, OS, and NVIDIA GPU detection
- Added `node_client/resource_guard.py`: CPU and memory resource limits
- Added `node_client/job_runner.py`: simulated sandboxed job runner
- Updated `node_client/client.py`: retry, heartbeat stability, resource guard, local logs
- Added `docs/NODE_CLIENT.md`: node client hardening guide

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## Current Structure

```text
index.html                    # English-first product MVP
api/main.py                   # FastAPI local scheduler/API skeleton
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

## Enable Real Local AI

Install Ollama and pull a local model:

```bash
ollama pull qwen2.5:3b
```

The `/ai/chat` endpoint will return `provider: ollama` when Ollama is running, and `provider: fallback` when it is not.

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
