# Owned Model Runbook

## Run full owned-mode app

Use the owned-mode entrypoint:

```bash
uvicorn api.main_owned:app --reload
```

Use the checked owned-mode entrypoint when you want artifact binding policy enforced before worker calls:

```bash
uvicorn api.main_owned_checked:app --reload
```

This includes:

```text
base Ailovanta API
data source registry
core result registry
owned model chat endpoint
artifact-binding checked owned model chat endpoint
```

## End-to-end path

```text
1. Register authorized data source.
2. Create public training job referencing that source.
3. Run ailovanta-core public bridge.
4. Register core result manifest in public API.
5. Register runtime model from that core result.
6. Register artifact binding with a reachable backend_ref.
7. Register trusted runtime node that has the model cached.
8. Call /ailovanta/v1/owned-chat-checked.
```

## Owned chat endpoints

```text
POST /ailovanta/v1/owned-chat
POST /ailovanta/v1/owned-chat-checked
```

The checked endpoint runs route policy before calling the worker:

```text
model_id + version
-> artifact binding lookup
-> backend_ref local check
-> runtime route
-> worker inference
```

If no verified Ailovanta runtime manifest or usable binding is available, the endpoint returns:

```text
owned_model_ready: false
source: owned-runtime-unavailable
```

If a verified Ailovanta runtime manifest is routed, the endpoint returns:

```text
owned_model_ready: true
```

## Boundary

`owned-chat` does not silently call the bootstrap local model. The checked endpoint additionally requires a usable artifact binding before worker inference.
