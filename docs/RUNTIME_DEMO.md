# Runtime Demo

This demo shows the visible product effect of the local Ailovanta runtime layer.

## Start API

```bash
uvicorn api.main:app --reload
```

## Run demo

```bash
python scripts/demo_runtime_flow.py --api-url http://127.0.0.1:8000
```

The script will:

1. Register a model manifest.
2. Register a runtime node with a cached model.
3. Route one request.
4. Print runtime status.
5. Print route history.

## Open dashboard

```text
http://127.0.0.1:8000/dashboard
```

## What this proves

The current MVP can already show the basic runtime loop:

```text
model manifest -> runtime node -> route request -> assignment history
```

This is still a local MVP, not a global production network. The next product step is to connect the dashboard directly to runtime status and provide a one-click seeded demo page.
