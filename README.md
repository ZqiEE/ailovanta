# Ailovanta Coding

[![Ailovanta CI](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml/badge.svg)](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml)

**One coding product for frontend, backend engineering, and repair.**

Ailovanta is a usable coding workspace backed by one local coding model and an owned-model training system. The public product is no longer a generic chat shell.

## Access policy

```text
Guest mode first.
No required login.
No required payment.
```

The first public version removes onboarding friction: users can open the product and start working on code without a login wall or paywall.

## Zero-cash operating mode

The default production path is designed to require **no paid model API or managed SaaS**. The operator still pays for the machine and domain, plus any electricity/bandwidth that the server provider bills separately.

```text
Required:
- one server
- one domain for public HTTPS

Runs on that server:
- FastAPI product API
- SQLite scheduler metadata
- local project storage
- Ollama model runtime
- optional Caddy HTTPS reverse proxy

Not required:
- OpenAI API
- Anthropic API
- Gemini API
- managed Redis
- managed PostgreSQL
- managed object storage
- paid TLS certificate
- paid monitoring/analytics service
```

`GET /coding/cost` reports whether the running process is still in zero-cash mode. It only returns names of detected external-service environment variables and never returns their secret values.

## Use it

A user can:

1. Create a project or import a local source folder.
2. Browse and edit project files in the browser.
3. Ask Ailovanta to build a feature, improve frontend UI, change backend code, or repair a bug.
4. Review the proposed file-level changes and full generated file contents.
5. Apply selected changes.
6. Inspect the project diff.
7. Download the modified project as a ZIP.

Generated Python/JSON/TOML/YAML/HTML changes are statically checked before any file in the changeset is written. A broken supported file rejects the entire apply operation.

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

The current public runtime is a bootstrap local coder through Ollama, defaulting to `qwen2.5-coder:7b`. This repository does **not** claim that the final proprietary three-stream distilled checkpoint has already been trained. The product runtime is deliberately checkpoint-agnostic so the bootstrap model can later be replaced by an owned Ailovanta checkpoint without changing the user workflow.

## Product architecture

```text
Browser coding workspace
        |
        v
FastAPI product API
        |
        +--> project store / files / diff / ZIP export
        |
        +--> SQLite local scheduler
        |
        +--> one local coding model through Ollama
        |
        +--> Frontend / Backend / Repair task modes
        |
        +--> three-expert autonomous training factory
```

The legacy distributed-compute infrastructure remains in the repository, but the production Coding process no longer imports the legacy application or requires its Redis/PostgreSQL options.

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
make install-coding
make api
```

Open:

```text
http://127.0.0.1:8000/
```

## Server deployment: CPU-compatible

```bash
make coding-up
make coding-model
make cost-status
```

The API is bound to `127.0.0.1:8000` on the host by default.

## Server deployment: NVIDIA GPU

Install the host NVIDIA driver and NVIDIA Container Toolkit, then:

```bash
make coding-gpu
make coding-model
make cost-status
```

`docker-compose.gpu.yml` only adds GPU access to the Ollama container; the rest of the product is unchanged.

## Public domain + automatic HTTPS

Point the domain's DNS record at the server, make ports 80/443 reachable, then run:

```bash
make coding-public AILOVANTA_DOMAIN=code.example.com
make coding-model
```

The `public` profile starts a self-hosted Caddy container. Caddy terminates HTTPS and proxies to the private API container, so a separate paid certificate or reverse-proxy SaaS is not required.

Project data is persisted in the `ailovanta_data` volume, model data in `ollama_data`, and Caddy certificate state in `caddy_data`.

## Main product APIs

```text
GET  /coding/status
GET  /coding/cost
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

The main CI compiles product modules and runs the complete pytest suite. RG additionally validates compose files, builds the lean production Docker image, and smoke-imports the real `api.product_app` from that image.
