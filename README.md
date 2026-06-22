# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v2.0 Data Engine Pack

Added:

- `api/source_registry.py`
- `api/corpus_pipeline.py`
- `api/web_document_store.py`
- `api/corpus_search.py`
- `api/training_candidate_store.py`
- `scripts/seed_authorized_corpus_demo.py`
- `scripts/corpus_report.py`
- `tests/test_corpus_pipeline.py`
- `tests/test_corpus_source_store.py`
- `make data-demo`
- `make data-report`

## v1.9 Report Store Pack

Added:

- `node_client/report_store.py`
- `scripts/list_worker_reports.py`
- `scripts/export_worker_reports.py`
- `docs/REPORTS.md`
- `tests/test_report_store.py`
- `make worker-reports`
- `make export-reports`

## Data Engine

```bash
make data-demo
make data-report
```

## Run Local Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## Docker

```bash
docker compose up --build
```
