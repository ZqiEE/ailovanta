# Ailovanta Native Run API

Ailovanta Native Run API is the primary local protocol for Ailovanta-specific execution.

## Endpoint

```text
POST /ailovanta/v1/run
```

## Why this exists

The native endpoint returns Ailovanta-specific fields that a generic chat endpoint does not expose:

- model id
- model version
- task type
- runtime route
- execution source
- usage data

## Start API

```bash
uvicorn api.main:app --reload
```

## Call it

```bash
curl -X POST http://127.0.0.1:8000/ailovanta/v1/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Ailovanta in one sentence.",
    "model_id": "ailovanta-local",
    "version": "local",
    "use_runtime_router": false
  }'
```

## Response shape

```json
{
  "object": "ailovanta.run",
  "model_id": "ailovanta-local",
  "version": "local",
  "task_type": "chat_completion",
  "answer": "...",
  "source": "ollama_or_fallback",
  "runtime_route": {},
  "usage": {
    "prompt_tokens": 1,
    "output_tokens": 1,
    "total_tokens": 2
  }
}
```

## Compatibility endpoint

Ailovanta also exposes:

```text
POST /v1/chat/completions
```

That endpoint is for existing client compatibility. The native endpoint is the main Ailovanta protocol.
