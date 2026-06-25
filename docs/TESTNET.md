# Testnet v0

This follows the original Ailovanta design:

```text
public node client
-> local resource guard
-> gateway registration
-> node admission check
-> runtime pool registration
-> task pull / result submit
-> proof / validation
-> artifact chunk manifest
-> route to verified warm runtimes
```

It is not a design where one official server owns all compute and storage. Nodes contribute spare compute, storage, and bandwidth without taking over the user's machine.

## Start API

```bash
uvicorn api.main_learning:app --reload
```

## Bootstrap a node

```bash
python -m node_client.testnet \
  --api-url http://127.0.0.1:8000 \
  --region global \
  --engine python \
  --engine local
```

This registers through:

```text
POST /nodes/register
POST /runtime/nodes/register
```

The machine becomes both:

```text
job worker node
runtime pool candidate
```

## Resource guard

Ailovanta Node should only use spare resources. The local guard checks:

```text
CPU usage
free system memory
GPU utilization
GPU memory usage
GPU temperature
Windows user idle time
battery / plugged-in status
```

Example safe contribution modes:

```bash
# Light: only after 5 minutes idle, conservative GPU use.
python -m node_client.client \
  --max-cpu-percent 35 \
  --max-gpu-percent 35 \
  --max-gpu-memory-percent 35 \
  --max-gpu-temperature-c 70 \
  --min-idle-seconds 300

# Balanced: default-like contribution, still pauses on heat/battery/high load.
python -m node_client.client \
  --max-cpu-percent 60 \
  --max-gpu-percent 60 \
  --max-gpu-memory-percent 60 \
  --max-gpu-temperature-c 75 \
  --min-idle-seconds 60

# High contribution: user explicitly allows heavier work.
python -m node_client.client \
  --max-cpu-percent 80 \
  --max-gpu-percent 80 \
  --max-gpu-memory-percent 80 \
  --max-gpu-temperature-c 78
```

Default behavior pauses on battery power. Use `--allow-on-battery` only when the user explicitly allows it.

## Pool selection

```text
no accelerator -> cpu_pool
< 24GB memory -> small_gpu_pool
>= 24GB memory -> large_gpu_pool
```

## Node admission

Before a node should be trusted as an active runtime, check admission:

```text
GET  /node-admission/rules
POST /node-admission/check
POST /node-admission/choose-pool
```

Admission checks:

```text
pool type
online status
GPU requirement
minimum GPU memory
trust score
current load
heartbeat freshness
trusted/private pool restrictions
```

## Runtime routing

```text
POST /runtime/models/register
POST /runtime/route
```

The router scores machines by:

```text
warm cache
trust score
current load
latency
price
region
privacy tier
```

## Artifact distribution

```bash
python scripts/chunk_manifest.py path/to/model-or-checkpoint.bin \
  --source node://node-1/cache/model.bin \
  --min-replicas 3
```

The manifest records:

```text
artifact_hash
chunk sha256 hashes
chunk sources
replica policy
```

The registry should store this small manifest, not the full model weights.

## Correct early testnet

```text
Machine A: gateway + private core bridge
Machine B: small_gpu_pool worker
Machine C: storage_pool seed/cache node
Machine D: validator_pool node
```

## Avoid

```text
Do not route every request to one official server.
Do not force every node to download every model.
Do not trust artifact sources without hash verification.
Do not send private/protected models to public nodes.
Do not run heavy GPU work while the user's machine is hot, busy, or on battery.
```

## Next implementation steps

```text
tiny training task shards
checkpoint pause/resume
validator mesh
reward/reputation updates
storage replica tracking
signed worker task envelopes
public testnet dashboard
```
