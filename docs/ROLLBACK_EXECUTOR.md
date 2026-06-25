# Rollback Executor

## Purpose

Rollback Executor turns a rollback action into a runtime status change.

It marks the bad candidate model as `rolled_back` and restores the previous model to `active` when the previous model is known.

## API

```text
POST /rollback/latest
POST /rollback/action
GET /rollback/logs
```

## CLI

```bash
python scripts/execute_rollback.py
```

## Flow

```text
live metrics
-> rollback-check
-> rollback action
-> rollback executor
-> candidate model status = rolled_back
-> previous model status = active
-> rollback log
```

## Full protection chain

```text
guarded learning
-> shadow registration
-> live registration
-> live metrics
-> rollback-check
-> rollback executor
```

## Meaning

Automatic learning now has an executable rollback path. A bad candidate does not only create an alert; it can be moved out of active runtime status.
