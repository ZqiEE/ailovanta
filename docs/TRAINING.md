# Training Jobs

v0.9 adds training job creation and model version registration.

This is still a local MVP skeleton. It does not perform real LoRA training yet. It defines the API shape and scheduler lifecycle needed before real training workers are added.

## Training job kinds

```text
rag_import
lora_micro
evaluation_batch
robot_memory_tune
```

## Create a training job

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "kind":"rag_import",
    "name":"demo-rag-import",
    "dataset_uri":"file://local/docs",
    "base_model":"qwen2.5:3b",
    "max_steps":100,
    "notes":"local MVP RAG import"
  }'
```

## List training jobs

```bash
curl http://127.0.0.1:8000/training/jobs
```

## Register a model version

```bash
curl -X POST http://127.0.0.1:8000/models/versions \
  -H "Content-Type: application/json" \
  -d '{
    "name":"private-ai-v0.1-local",
    "base_model":"qwen2.5:3b",
    "source_job_id":"train_xxxxxxxx",
    "notes":"first local model version record"
  }'
```

## List model versions

```bash
curl http://127.0.0.1:8000/models/versions
```

## Next steps

- Add real RAG importer
- Add LoRA/QLoRA worker integration
- Add model artifact paths
- Add evaluation reports
- Add version promotion rules
- Add signed model metadata
