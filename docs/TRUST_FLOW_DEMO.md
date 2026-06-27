# Trust Flow Demo

This demo proves the decentralized artifact path without treating the API server as the final source of truth.

## Start API

Strict local demo with mock notary:

```bash
export AILOVANTA_CHAIN_ANCHOR=http
export AILOVANTA_CHAIN_ANCHOR_URI=http://127.0.0.1:8000/notary/mock/anchor
export AILOVANTA_NODE_SECRETS_JSON='{"demo-node":"demo-secret"}'
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

PowerShell:

```powershell
$env:AILOVANTA_CHAIN_ANCHOR="http"
$env:AILOVANTA_CHAIN_ANCHOR_URI="http://127.0.0.1:8000/notary/mock/anchor"
$env:AILOVANTA_NODE_SECRETS_JSON='{"demo-node":"demo-secret"}'
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

## Run full trust flow

Strict receipt verification is the default:

```bash
python scripts/demo_trust_flow.py
```

Loose mode is only for debugging an API that has no node secret configured:

```bash
python scripts/demo_trust_flow.py --loose
```

## What it does

```text
create local demo artifact
-> /artifacts/store
-> signed worker receipt
-> /catalog/from-receipt
-> /catalog/items/{id}/validate
-> /catalog/items/{id}/notarize
-> /catalog/items/{id}/publish
-> /runtime/local/load
-> /runtime/local/generate
```

## Trust objects

The server indexes metadata, but the trust path is:

```text
artifact_uri
artifact_hash
worker receipt
anchor_receipt
runtime manifest
```

## Gate rules

Publish should fail unless:

```text
artifact_hash starts with sha256:
worker receipt is valid
worker receipt checkpoint_hash matches artifact_hash
anchor_receipt exists
anchor_receipt references the same hash
```

## Production replacements

Replace demo adapters with durable systems:

```text
AILOVANTA_ARTIFACT_STORE=s3 | r2 | minio | external
AILOVANTA_ARTIFACT_STORE_URI=s3://bucket/prefix
AILOVANTA_CHAIN_ANCHOR=notary | external | http
AILOVANTA_CHAIN_ANCHOR_URI=https://your-notary-or-chain-gateway/anchor
AILOVANTA_CONTENT_GATEWAY=https://ipfs.io/ipfs
```

Postgres and Redis are coordination/index layers only.
