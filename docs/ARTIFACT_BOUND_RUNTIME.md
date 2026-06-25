# Artifact Bound Runtime

## Purpose

Artifact Bound Runtime is the worker-side loader for artifact bindings.

It tries to resolve:

```text
model_id + version
-> artifact binding
-> backend_ref
-> local checkpoint or transformers model directory
-> worker response
```

## Supported binding kinds

```text
checkpoint-artifact    reads local checkpoint metadata when backend_ref is file:// or a local path
jsonl-stat             same as checkpoint-artifact for lightweight checkpoint outputs
transformers-local     loads a local Transformers model directory
transformers-causal-lm loads a local Transformers model directory
```

## Worker order

```text
1. artifact-bound runtime
2. configured model backend client
3. Ollama local runtime fallback
```

## Important reality

A jsonl-stat checkpoint is not a full conversational model. When the binding points to a lightweight checkpoint, the worker returns checkpoint-bound status and metadata instead of pretending to generate as a large model.

A real generative path requires a binding whose `backend_kind` is `transformers-local` or `transformers-causal-lm` and whose `backend_ref` points to a valid local model directory.

## Example binding

```json
{
  "model_key": "ailovanta-owned:candidate",
  "artifact_hash": "sha256:...",
  "checkpoint_uri": "file:///path/to/checkpoint.bin",
  "backend_kind": "checkpoint-artifact",
  "backend_ref": "file:///path/to/checkpoint.bin",
  "status": "active"
}
```

## Meaning

Owned chat can now be artifact-aware. It can prefer a bound artifact backend before falling back to other local runtimes.
