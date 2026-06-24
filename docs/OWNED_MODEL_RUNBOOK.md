# Owned Model Runbook

## Run full owned-mode app

Use the owned-mode entrypoint:

```bash
uvicorn api.main_owned:app --reload
```

This includes:

```text
base Ailovanta API
data source registry
core result registry
owned model chat endpoint
```

## End-to-end path

```text
1. Register authorized data source.
2. Create public training job referencing that source.
3. Run ailovanta-core public bridge.
4. Register core result manifest in public API.
5. Register runtime model from that core result.
6. Register trusted runtime node that has the model cached.
7. Call /ailovanta/v1/owned-chat.
```

## Owned chat endpoint

```text
POST /ailovanta/v1/owned-chat
```

If no verified Ailovanta runtime manifest is available, the endpoint returns:

```text
owned_model_ready: false
source: owned-runtime-unavailable
```

If a verified Ailovanta runtime manifest is routed, the endpoint returns:

```text
owned_model_ready: true
source: ailovanta-owned-runtime
```

## Boundary

`owned-chat` does not silently call the bootstrap local model. It requires runtime routing to an Ailovanta model manifest.
