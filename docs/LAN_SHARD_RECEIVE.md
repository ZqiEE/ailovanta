# LAN shard receive flow

This is the first node-side shard receiving layer.

## Worker node

Start the worker on Computer B:

```bash
uvicorn api.demo_worker_app:app --host 0.0.0.0 --port 9001
```

The worker now exposes:

```text
POST /v1/shards/receive
GET  /v1/shards
```

## Receive payload

```json
{
  "artifact_hash": "sha256:artifacthash",
  "shard_index": 0,
  "shard_hash": "sha256:shardhash",
  "data_base64": "...",
  "source_runtime_id": "coordinator"
}
```

The worker verifies the shard hash before saving it. If the hash does not match, the shard is rejected and not written to disk.

Accepted shards are stored under:

```text
runtime_data/received_shards/
```

## Check worker shards

```bash
curl http://WORKER_IP:9001/v1/shards
```

## Boundary

This implements verified node-side receiving. The next layer is coordinator-side automatic shard transfer or worker-side shard pull. Direct automatic transfer code may require extra safety controls, because it sends local files over HTTP.
