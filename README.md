# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Free access attracts users, users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v0.4 Update

v0.4 moves the project from product skeleton to local runtime skeleton.

### What changed

- Added `api/main.py`: FastAPI scheduler/API skeleton
- Added `node_client/client.py`: local node client simulation
- Added `requirements.txt`: Python runtime dependencies
- Added `docs/LOCAL_RUNTIME.md`: local runtime guide
- Added API endpoints for node registration, heartbeat, job dispatch, result submit, AI chat, and network status

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## Current Structure

```text
index.html                 # English-first product MVP
api/main.py                # FastAPI local scheduler/API skeleton
node_client/client.py      # Local node client skeleton
docs/ARCHITECTURE.md       # Architecture notes
docs/ROADMAP.md            # Product roadmap
docs/LOCAL_RUNTIME.md      # Local runtime instructions
validate.py                # Static repository validation
requirements.txt           # Python dependencies
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
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
