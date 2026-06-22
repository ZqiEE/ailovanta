# Node Client

v0.6 hardens the local node client. It is still a local MVP skeleton, but the client is now structured like a real worker.

## Features

- Device detection
- NVIDIA GPU detection via `nvidia-smi` when available
- Resource guard for CPU and free memory
- Heartbeat stability
- Request retry with backoff
- Simulated sandboxed job runner
- Local log file under `runtime_data/logs/node.log`

## Run API

```bash
uvicorn api.main:app --reload
```

## Run Node

```bash
python node_client/client.py \
  --api-url http://127.0.0.1:8000 \
  --contribution 30 \
  --poll-seconds 5 \
  --max-cpu-percent 70 \
  --min-free-memory-gb 1.5
```

## What the node does

1. Detects device profile
2. Registers itself with the API
3. Sends heartbeat events
4. Checks local resource limits
5. Pulls the next eligible job
6. Runs the simulated job runner
7. Submits job result
8. Writes logs locally

## Important production gaps

This is not production ready yet. Before real public nodes, the project still needs:

- Signed jobs
- Sandboxed execution
- Network authentication
- Abuse prevention
- Encrypted transport
- Persistent node identity
- GPU workload isolation
- Real task verification
