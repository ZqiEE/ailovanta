# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local static MVP for a **user-owned GPU network for private AI**. Free access attracts users, users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v0.3 Update

v0.3 moves the project from a polished demo into a more realistic product skeleton.

### What changed

- Added Node Client page: device scan, resource cap, heartbeat, worker loop
- Added API page: scheduler, node registration, job dispatch, result submit
- Added Protocol page: contributor access, node reputation, task verification
- Added Pricing page: contributor free, paid user, builder API, enterprise/private pool
- Added Waitlist page: local demo waitlist stored in browser
- Updated roadmap and validation checks

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## MVP Features

- Contributor mode: run a GPU/CPU node and use AI for free
- Paid mode: use AI without running a node
- Node client simulation
- Scheduler/API skeleton
- Compute network dashboard
- Private AI chat demo
- Ephemeral prompts, replies, chat records, and robot memory
- Local robot memory with one-click wipe
- Training engine simulation: RAG, data cleaning, LoRA/QLoRA, task dispatch, model merge
- Investor narrative: user growth → compute growth → lower cost → better AI → more users

## Run Locally

Double click:

```text
index.html
```

Or run:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Roadmap

1. Add real Ollama + Qwen/Llama local inference
2. Build Python/Rust node client
3. Build FastAPI scheduler
4. Add PostgreSQL node/user system
5. Add Redis task queue
6. Add robot SDK and local-first memory

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
