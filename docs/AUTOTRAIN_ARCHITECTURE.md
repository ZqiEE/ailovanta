# AutoTrain Architecture

Ailovanta AutoTrain turns authorized public learning events into runtime-ready model candidates.

## Responsibilities

AutoTrain is responsible for:

```text
discover trainable events
-> build training pack
-> create foundation job
-> call ailovanta-core training/eval
-> finalize artifact metadata
-> verify artifact digest
-> pass promotion gate
-> import candidate into owned runtime
-> prepare warm runtime route
```

## Current entrypoints

AutoTrain is now mounted in the release-ready app:

```text
POST /learning/events       # collect public learning event rows
POST /autotrain/pack        # build/reuse an AutoTrain pack from events
POST /autotrain/run         # run event -> pack -> guarded learning -> runtime import
GET  /autotrain/status      # inspect AutoTrain readiness
```

CLI:

```bash
python scripts/autotrain.py --core-path ../ailovanta-core --execute-checkpoints
```

For a real backend run, pass a core path plus backend settings:

```bash
python scripts/autotrain.py \
  --core-path ../ailovanta-core \
  --model-backend local \
  --base-model qwen2.5:3b \
  --backend-device cuda \
  --backend-max-steps 100 \
  --execute-checkpoints
```

## Required default

Every training job created by AutoTrain must include:

```text
distributed_required=true
```

Local execution is allowed only as a controlled distributed simulation. The public API and core importer must still treat the task as distributed.

## Node classes

- CPU nodes: data cleaning, license checks, repository parsing, deduplication, benchmark building.
- Small GPU nodes: embedding, teacher sampling, code explanation generation, small adapter jobs.
- Strong GPU nodes: QLoRA, LoRA, adapter training, batch inference, candidate model update.
- Validator nodes: pytest, lint, typecheck, sandbox execution, benchmark scoring.
- Aggregator: merges candidate results and computes promotion metrics.
- Runtime nodes: load model manifests, keep warm caches, serve Ailovanta-Code responses.

## Promotion

A model candidate can become runtime-visible only after validation and promotion gate checks pass. Failing candidates remain audit records and must not be presented as active production models.

## Boundary

This is an automatic training loop, not a claim that a GPT-scale model is already trained. Real improvement requires real learning events, `ailovanta-core`, a configured training backend, and usable checkpoint artifacts.
