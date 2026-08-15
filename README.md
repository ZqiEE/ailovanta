# Ailovanta Coding

[![Ailovanta CI](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml/badge.svg)](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml)

**Your GPU. Your code. One coding model for frontend, backend engineering, and repair.**

Ailovanta is being rebuilt around a simple rule: the normal user should not need to understand local-model deployment, quantization, context settings, CUDA tuning, or model routing just to use the GPU they already own.

## Access policy

```text
Guest mode first.
No required login.
No required payment.
```

Private-local use has no account or paywall requirement. Community compute is a separate explicit opt-in action.

## Primary product mode: private local

The default user path runs on the user's own computer:

```text
browser workspace
    -> local FastAPI
    -> local project files
    -> local Ollama
    -> user's own GPU / CPU
```

In `private-local` mode:

- project files stay on that computer;
- prompts stay on that computer;
- model output stays on that computer;
- OpenAI / Anthropic / Gemini APIs are not required;
- telemetry is not required;
- the UI binds to loopback by default;
- the selected checkpoint is visible and verifiable by the user.

Run it:

### macOS / Linux

```bash
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
bash start-local.sh
```

### Windows PowerShell

```powershell
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
.\start-local.ps1
```

The launcher creates a local Python environment, detects available hardware, starts/reuses local Ollama, chooses a practical model profile, offers the one-time model download when needed, starts Ailovanta on `127.0.0.1:8765`, and opens the workspace.

You can also run:

```bash
make install-coding
make local
```

## Hardware-aware bootstrap models

The final product target is an Ailovanta-owned unified checkpoint. Until that checkpoint is trained, local mode automatically selects an open bootstrap coder according to the machine rather than forcing every user onto one model size.

Current policy is approximately:

```text
22GB+ NVIDIA VRAM + 32GB+ RAM -> qwen3-coder:30b
14GB+ NVIDIA VRAM             -> qwen2.5-coder:14b
8GB+ NVIDIA VRAM              -> qwen2.5-coder:7b
Apple Silicon 48GB+           -> qwen3-coder:30b
Apple Silicon 24GB+           -> qwen2.5-coder:14b
16GB+ system RAM              -> qwen2.5-coder:7b
lower-memory fallback         -> qwen2.5-coder:3b
```

The policy deliberately leaves memory for KV cache and the workspace instead of selecting the largest model that can barely load. Users can override model/context from the local launcher.

## Why this is not just Ollama with a UI

The product adds a software-engineering layer around the local model:

1. repository-aware context selection instead of dumping the whole repo into a small model;
2. Frontend / Backend / Repair behavior modes using the same deployed checkpoint;
3. complete file-level changesets instead of chat snippets;
4. a second local self-review pass by default;
5. static validation before any generated file is written;
6. transactional apply with rollback if a batch fails midway;
7. selective apply, project diff, and ZIP export;
8. no claim that commands/tests ran unless execution evidence exists.

The second review pass costs additional local inference time but no model-API money. Set `AILOVANTA_SELF_REVIEW=false` to disable it.

## Public server: control plane, not inference plane

The public domain does **not** need a GPU or Ollama. Its job is to distribute the product and coordinate the opt-in network.

```text
public domain
    -> Caddy HTTPS
    -> FastAPI control plane
    -> SQLite scheduler / node metadata
```

Deploy with only a server + domain:

```bash
make control-public AILOVANTA_DOMAIN=code.example.com
```

`docker-compose.control.yml` starts no model runtime. Caddy provides automatic HTTPS. No managed PostgreSQL, managed Redis, paid TLS certificate, object-storage SaaS, analytics SaaS, or commercial model API is required for the baseline deployment.

In `control-plane` mode the private `/coding/projects` and model-generation routes are not registered at all, so the public domain is not an accidental private-code upload endpoint.

## Optional community compute

A user may explicitly opt in to contribute idle CPU/GPU resources:

```bash
python -m node_client.client_real --api-url https://code.example.com --contribution 30
```

The CLI displays the contribution disclosure and requires confirmation. Non-interactive operation requires the explicit `--accept-public-compute` flag.

Community workers:

- do not upload the machine hostname;
- receive a random node identity and a private device token;
- authenticate heartbeats, job claims, and result submissions with that device token;
- report only scheduling-relevant machine capability such as GPU model/memory;
- obey CPU/GPU/memory/temperature/battery limits;
- can run real `coding_inference` through their own local Ollama;
- reject `private` or unlabeled coding-inference payloads in worker policy;
- currently accept only `public` or `synthetic` coding-inference scopes.

Public node discovery is de-identified. Raw node IDs, local hostnames, and job prompts are not returned by the public node/status endpoints.

Private repository inference is **not** sent to random community nodes. Private work belongs on the owner's own Ailovanta Local runtime unless a future explicitly trusted/encrypted mode is selected.

### Public inference queue protection

`POST /jobs/public-inference` is disabled by default. To let an internal product/training service enqueue public or synthetic tasks, configure an operator secret:

```bash
export AILOVANTA_PUBLIC_INFERENCE_TOKEN='a-long-random-secret'
make control-public AILOVANTA_DOMAIN=code.example.com
```

The producer sends that value in `X-Ailovanta-Job-Token`. The same protected token is required to inspect job metadata or fetch completed inference results. Public callers cannot freely queue work onto contributor GPUs.

## Product workflow

A user can:

1. create a project or import a source folder;
2. browse and edit project files;
3. ask Ailovanta to build a feature, improve frontend UI, change backend code, or repair a bug;
4. let the same local model generate and self-review a file-level proposal;
5. inspect every generated file before applying it;
6. apply selected files transactionally;
7. inspect the unified project diff;
8. download the modified project as a ZIP.

Generated Python/JSON/TOML/YAML/HTML changes are statically checked before any file in the changeset is written. Import and edit limits are advertised by `/coding/status`, and the browser importer follows those configured limits rather than hard-coded demo sizes.

## One model, three strengths

The product exposes:

```text
Auto
Frontend
Backend
Repair / Debug
```

These modes use the **same deployed checkpoint**. They are not runtime routing to Gemini, Claude, or Codex.

The owned-model training target is:

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

The repository does **not** claim that the proprietary three-stream distilled checkpoint already exists. Open bootstrap models are temporary runtime weights; the surrounding product, verifier, distributed network, and training architecture are designed so the owned checkpoint can replace them later without changing the user workflow.

## Zero-cash baseline

For the company/operator, baseline required cash infrastructure is intended to be:

```text
required:
- one ordinary public server
- one domain

not required:
- central inference GPU
- OpenAI API
- Anthropic API
- Gemini API
- managed Redis
- managed PostgreSQL
- managed object storage
- paid TLS certificate
- paid monitoring/analytics service
```

This does not mean computation has no physical cost: users/contributors consume their own electricity and hardware resources, and the public server still has its normal hosting/bandwidth cost. `GET /coding/cost` in a local coding runtime, or `GET /control/status` on the public control plane, reports the configured zero-cash runtime mode without exposing secret values.

## Main APIs

Private/local product:

```text
GET  /coding/status
GET  /coding/privacy
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

Distributed control plane:

```text
GET  /control/status
POST /nodes/register
POST /nodes/heartbeat
GET  /network/status
GET  /network/nodes
GET  /jobs/next
GET  /jobs/{job_id}             # protected producer token
GET  /jobs/{job_id}/result      # protected producer token
POST /jobs/result               # authenticated node token
POST /jobs/public-inference     # protected producer token; disabled by default
```

Training-system APIs remain available on non-control local/development runtimes:

```text
GET  /coding/experts
POST /coding/training/expert
POST /coding/training/next
POST /coding/training/unify
```

## Validation

```bash
make validate
```

CI compiles the product, runs the complete pytest suite, validates deployment configuration, builds the lean production image, and smoke-imports the real `api.product_app`.

See `docs/CODING_REBUILD.md` for the specialist/unification design. The private `ailovanta-core` repository retains H-SwarmTrain and the deeper distributed training core.
