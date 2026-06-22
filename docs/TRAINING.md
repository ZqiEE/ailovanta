# Training Jobs

v0.9 adds training job creation and model version registration.

## Training job kinds

```text
rag_import
lora_micro
evaluation_batch
private_memory_tune
```

## Create a training job

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{"kind":"rag_import","name":"demo-rag","dataset_uri":"file://local/docs","base_model":"qwen2.5:3b"}'
```

## Register a model version

```bash
curl -X POST http://127.0.0.1:8000/models/versions \
  -H "Content-Type: application/json" \
  -d '{"name":"private-ai-v0.1-local","base_model":"qwen2.5:3b","source_job_id":"train_xxxxxxxx"}'
```

## Next steps

- Real RAG importer
- LoRA/QLoRA worker integration
- Model artifact paths
- Evaluation reports
- Version promotion rules
