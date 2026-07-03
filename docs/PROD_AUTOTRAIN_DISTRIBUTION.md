# Production AutoTrain and artifact distribution

This is the first production-control-plane version. It is not the final global network yet.

## Production AutoTrain

Endpoint:

```text
POST /production-autotrain/run
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/production-autotrain/run \
  -H "Content-Type: application/json" \
  -d '{"core_path":"../ailovanta-core","execute_checkpoints":true,"model_backend":"transformers-causal-lm","base_model":"sshleifer/tiny-gpt2","backend_device":"auto","backend_max_steps":5,"allow_shadow_import":true,"score_fallback":0.5,"min_delta":0.0}'
```

What it does:

```text
AutoTrain -> metrics -> proof -> best-score comparison -> audit file
```

A candidate that does not beat the previous best score is rejected by proof instead of silently replacing the active model.

Audit files are written under:

```text
runtime_data/production_autotrain/
```

## Artifact sharding

Endpoint:

```text
POST /artifact-shards/build
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/artifact-shards/build \
  -H "Content-Type: application/json" \
  -d '{"path":"runtime_data/model_backend/pytorch_model.bin","chunk_size":1048576}'
```

This creates shard files plus a manifest with shard hashes and the full artifact hash.

## Placement planning

Endpoint:

```text
POST /artifact-placement/plan
```

The planner reads online runtime nodes and assigns each shard to runtime nodes with a replication factor.

## Current boundary

Implemented now:

- LAN runtime contributors can join.
- training candidates get score proof and audit records.
- artifact files can be split into verifiable shards.
- shard placement can be planned across online runtime nodes.

Not finished yet:

- shard transfer to remote workers
- node-side shard receive API
- NAT traversal
- anti-cheat and data poison resistance
- multi-node training execution
