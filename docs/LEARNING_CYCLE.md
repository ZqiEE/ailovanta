# Learning Cycle

## Purpose

This is the public-side bridge for autonomous learning.

It collects runtime events, exports them for core scoring, imports the scored training pack, and makes the latest pack available for the foundation pipeline.

## App entrypoint

```bash
uvicorn api.main_learning:app --reload
```

This includes:

```text
owned chat
parcel distribution
learning event API
```

## API

```text
POST /learning/events
GET /learning/events
POST /learning/export
POST /learning/runs
GET /learning/runs/latest
GET /learning/packs/latest
```

## Run a learning cycle

```bash
python scripts/run_learning_cycle.py --core-path ../ailovanta-core
```

## Flow

```text
public runtime event
-> /learning/events
-> /learning/export
-> core scripts/run_autotruth.py
-> autotruth result
-> /learning/runs
-> latest training pack
```

## Next step

Turn the latest training pack into a foundation job automatically, then pass it into the existing foundation pipeline.
