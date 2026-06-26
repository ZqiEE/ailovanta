# Model storage and GitHub code ingestion plan

## Where the model is saved

Ailovanta must not save large model weights inside SQLite, Postgres, or a single central API server.

The agreed design is:

```text
Model Registry: small metadata only
Artifact Storage: real model files and chunks
Runtime Nodes: hot cached models/adapters
Storage Nodes: replicated cold model chunks
Validator Nodes: verify hashes, deltas, evals
Access Router: chooses where to load/run the model
```

## Current local MVP storage

For the current local testnet:

```text
runtime_data/model_deltas/<plan_id>/*.pt
  training shard outputs from worker nodes

runtime_data/merged_models/*.pt
  merged local checkpoint built by scripts/mck.py or /ck/build

runtime_data/didx.json
  verified delta index from scheduler results

runtime_data/credits.json
  contribution credits for nodes with verified deltas

runtime_data/scheduler.sqlite3
  job/result/node metadata only, not model weights
```

The `.pt` files are the actual model/delta files. SQLite only records jobs, results, verification metadata, and routing state.

## Production storage target

For production:

```text
merged checkpoint
-> split into chunks
-> content-address each chunk by sha256/CID
-> replicate chunks across storage_pool nodes
-> optionally seed from object storage/IPFS-like storage
-> registry stores manifest only
```

The model registry stores:

```text
model_id
version
manifest_hash
artifact/chunk references
chunk hashes
license/data lineage summary
evaluation score
runtime tier
signature
status
```

The registry does not store full model weights.

## Runtime loading flow

```text
chat / run request
-> access router selects runtime node
-> runtime node checks manifest
-> runtime node checks local chunk cache
-> missing chunks downloaded from storage_pool / mirrors / seeds
-> each chunk verified by hash
-> checkpoint or adapter loaded
-> inference/training runs
-> result sampled by validators
-> usage and rewards recorded
```

## GitHub code-first training plan

Ailovanta should learn code first because code quality can be evaluated automatically:

```text
syntax compile
unit tests
type checks
lint checks
bug-fix benchmarks
patch repair tasks
```

The first data sources should be:

```text
user-owned repositories
organization-owned repositories with permission
public repositories with permissive licenses
approved allowlist repositories
public domain / clearly allowed examples
```

## Not blind whole-GitHub scraping

Do not start with uncontrolled scraping of all GitHub pages. The crawler must avoid:

```text
private repos without permission
unclear-license code
secret/API key leakage
personal data
vendored dependencies
node_modules / .venv / build output
duplicate forks
malware / exploit-only repos
rate-limit abuse
excessive bandwidth use
```

## GitHub ingestion architecture

```text
repo discovery
-> license check
-> clone/fetch allowed repo
-> secret scan
-> file type filter
-> dedupe by hash
-> code quality score
-> write code_corpus.jsonl
-> shard into model_shard jobs
-> train deltas on nodes
-> verify deltas
-> merge checkpoint
-> evaluate coding ability
-> promote if score improves
```

## Data manifest for every record

Every code training record should include:

```text
source_url / repo
commit_sha
path
language
license_hint
content_hash
bytes
quality_score
secret_scan_status
created_at
```

## Current commands

Build local code corpus:

```bash
python scripts/code_corpus.py \
  --source . \
  --output runtime_data/code_corpus.jsonl
```

Train code-first loop:

```bash
python scripts/train_code_loop.py \
  --api-url http://127.0.0.1:8000 \
  --source . \
  --total-tokens 4096 \
  --shard-tokens 512 \
  --node-runs 8
```

Run merged checkpoint:

```bash
python scripts/rck.py --text "Write a FastAPI login route"
```

## Next implementation steps

```text
1. Add secret scanner before corpus write.
2. Add repo allowlist file.
3. Add GitHub repo fetcher for allowed repos.
4. Add license filter.
5. Add code eval harness.
6. Add artifact chunk manifest for merged checkpoints.
7. Add storage_pool replication tracker.
8. Register promoted checkpoints in model registry.
```
