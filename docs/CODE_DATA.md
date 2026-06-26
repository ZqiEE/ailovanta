# Code-first data strategy

Ailovanta should not start with random whole-web scraping. The useful path is:

```text
trusted / allowed code sources
-> code corpus builder
-> shard jobs
-> verified deltas
-> merged code checkpoint
-> code-first runtime
```

## Why code first

Code ability is easier to evaluate than general chat:

```text
unit tests
syntax checks
type checks
lint checks
benchmark prompts
repository repair tasks
```

That means Ailovanta can improve through measurable feedback instead of only subjective chat scoring.

## Source policy

Preferred sources:

```text
user-owned repositories
company-owned repositories with permission
public repositories with clear permissive licenses
public domain / permissive examples
docs and code snippets explicitly allowed for training/use
```

Avoid by default:

```text
private code without permission
unclear-license code
sites that disallow automated access
credentials, secrets, API keys, tokens
personal data inside repositories
large vendored dependency folders
node_modules / .venv / build artifacts
```

## Local code corpus

Build a code corpus from a local folder:

```bash
python scripts/code_corpus.py \
  --source . \
  --output runtime_data/code_corpus.jsonl
```

Train code-first local loop:

```bash
python scripts/train_code_loop.py \
  --api-url http://127.0.0.1:8000 \
  --source . \
  --total-tokens 4096 \
  --shard-tokens 512 \
  --node-runs 8
```

Outputs:

```text
runtime_data/code_corpus.jsonl
runtime_data/model_deltas/<plan_id>/*.pt
runtime_data/didx.json
runtime_data/credits.json
runtime_data/merged_models/*.pt
```

## Future web ingestion

Automatic web ingestion should be a policy-controlled crawler, not blind scraping:

```text
seed URLs / allowed domains
robots and rate limits
content hash deduplication
license / terms metadata
secret scanning
PII filtering
poison filtering
source manifest
opt-out / removal list
```

The first production crawler should only add sources that pass the manifest policy. The crawler should write source metadata beside every training record.

## Evaluation first

For code training, every checkpoint should be evaluated by:

```text
Python syntax compile
TypeScript build / typecheck where available
unit tests where available
patch-based repair tasks
known coding benchmarks
security pattern checks
```

Only checkpoints that improve code evals should be promoted.
