# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v1.5 Usage Metering Pack

Includes v1.4 Reputation Pack plus local event metering.

Added in v1.5:

- `api/usage_store.py`
- `POST /usage/events`
- `GET /usage/events`
- `GET /usage/summary`
- `usage.html`
- `scripts/simulate_usage.py`
- `scripts/export_usage.py`
- `docs/METERING.md`
- `tests/test_usage.py`
- `tests/test_usage_api.py`

Existing packs:

- v1.4 Reputation Pack
- v1.3 Node Identity Pack
- v1.2 Dashboard Pack
- v1.1 Operations Pack
- **v1.0 Engineering Pack**

Main scope:

- Open GPU Network
- Private AI Runtime
- Node Client
- Scheduler
- Queue and Verification
- Training Jobs
- Model Version Registry
- Local Dashboard
- Node Reputation
- Usage Metering

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

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

## Usage Metering

```bash
python scripts/simulate_usage.py --api-url http://127.0.0.1:8000
curl http://127.0.0.1:8000/usage/summary
python scripts/export_usage.py --api-url http://127.0.0.1:8000
```

Open:

```text
usage.html
```

## Reputation

```bash
curl http://127.0.0.1:8000/reputation/leaderboard
curl http://127.0.0.1:8000/reputation/summary
python scripts/export_reputation.py --api-url http://127.0.0.1:8000
```

## Node Identity

```bash
python scripts/show_node_identity.py
python node_client/client.py --api-url http://127.0.0.1:8000 --identity-path runtime_data/node_identity.json
```

## Dashboard

Open:

```text
dashboard.html
```

The dashboard reads:

```text
http://127.0.0.1:8000/dashboard/summary
```

## Docker

```bash
docker compose up --build
```
