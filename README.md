# Ailovanta Coding

[![Ailovanta CI](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml/badge.svg)](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml)

**One coding product for frontend, backend engineering, and repair.**

Ailovanta is being rebuilt as a usable coding workspace backed by one local coding model and an owned-model training system. The public product is no longer a generic chat shell.

## Use it

A user can:

1. Create a project or import a local source folder.
2. Browse and edit project files in the browser.
3. Ask Ailovanta to build a feature, improve frontend UI, change backend code, or repair a bug.
4. Review the proposed file-level changes.
5. Apply selected changes.
6. Inspect the project diff.
7. Download the modified project as a ZIP.

Ailovanta does **not** execute arbitrary uploaded repository code on the central server. The current public product edits source safely; isolated execution belongs on sandboxed workers.

## One model, three strengths

The product exposes four work modes:

```text
Auto
Frontend
Backend
Repair / Debug
```

These modes use the **same deployed checkpoint**. They are not runtime routing to Gemini, Claude, or Codex.

The training architecture has three specialist branches:

```text
Frontend specialist
  -> visual UI / browser / responsive / interaction quality

Backend specialist
  -> repository engineering / APIs / databases / tests

Repair specialist
  -> reproduce / diagnose / patch / regression control

three same-base specialists
  -> unification
  -> one Ailovanta-owned coding checkpoint
```

The current public runtime is a bootstrap local coder through Ollama, defaulting to `qwen2.5-coder:7b`. This repository does **not** claim that the final proprietary three-stream distilled checkpoint has already been trained. The training, verification, checkpoint, and unification paths are being built so the bootstrap model can later be replaced by the owned Ailovanta checkpoint without changing the product workflow.

## Product architecture

```text
Browser coding workspace
        |
        v
FastAPI product API
        |
        +--> project store / files / diff / ZIP export
        |
        +--> one local coding model through Ollama
        |
        +--> Frontend / Backend / Repair task modes
        |
        +--> existing scheduler / node / verifier infrastructure
        |
        +--> three-expert autonomous training factory
```

The old distributed-compute infrastructure is retained underneath the coding product: node registration, job scheduling, verification, trust, artifacts, runtime routing, training jobs, checkpoint promotion, and H-SwarmTrain direction.

## Local quickstart

Install Ollama and pull the bootstrap coder:

```bash
ollama pull qwen2.5-coder:7b
```

Then:

```bash
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make validate
make api
```

Open:

```text
http://127.0.0.1:8000/
```

Windows PowerShell:

```powershell
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m compileall -q api node_client scripts
python -m pytest -q
uvicorn api.product_app:app --reload
```

## Minimal server deployment

A dedicated production compose is included:

```bash
docker compose -f docker-compose.coding.yml up -d --build
docker compose -f docker-compose.coding.yml exec ollama ollama pull qwen2.5-coder:7b
curl http://127.0.0.1:8000/coding/status
```

`docker-compose.coding.yml` binds the application to localhost. Put Caddy, Nginx, or another TLS reverse proxy in front of port `8000` and point the domain at the server.

Project data is persisted in the `ailovanta_data` volume and Ollama model data in `ollama_data`.

## Main product APIs

```text
GET  /coding/status
POST /coding/projects
GET  /coding/projects
GET  /coding/projects/{project_id}
GET  /coding/projects/{project_id}/file
PUT  /coding/projects/{project_id}/file
DELETE /coding/projects/{project_id}/file
POST /coding/projects/{project_id}/import
POST /coding/projects/{project_id}/propose
POST /coding/projects/{project_id}/apply
GET  /coding/projects/{project_id}/diff
GET  /coding/projects/{project_id}/export
```

Training-system APIs remain available:

```text
GET  /coding/experts
POST /coding/training/expert
POST /coding/training/next
POST /coding/training/unify
```

## Training target

The long-term model target is deliberately narrow: a small, high-capability software-engineering model rather than a general-purpose encyclopedia model.

```text
strong frontend product work
+ strong repository/backend engineering
+ strong debugging/repair
+ executable verification
+ autonomous improvement
= one owned Ailovanta coding model
```

See `docs/CODING_REBUILD.md` for the specialist/unification design. The private `ailovanta-core` repository retains the distributed training core and H-SwarmTrain infrastructure.

## Validation

```bash
make validate
```

The main CI compiles product modules and runs the complete pytest suite. Release and RG gates additionally verify the product surface and legacy infrastructure compatibility.
