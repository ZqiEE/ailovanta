# Auto Runtime Preparation

## Local command

```bash
python scripts/run_auto_local.py \
  --core-path ../ailovanta-core \
  --execute-checkpoints \
  --model-backend jsonl-stat
```

## Status summary

```bash
python scripts/show_auto_status.py
```

## Flow

```text
learning events
-> AutoTruth
-> guarded learning
-> foundation import
-> doctor before prepare
-> model runtime preparation
-> doctor after prepare
-> run log
```

## Result fields

```text
doctor_before_prepare
runtime_prepare
doctor_after_prepare
```

This lets the autonomous loop show whether the model is actually ready to route after learning.
