# Ailovanta Local — direct use

Ailovanta Local is the primary private coding mode. The web UI, project copy, prompt, model inference, and generated code all run on the same computer.

## Requirements

- Python 3.11+
- Ollama installed on this computer
- enough local RAM/VRAM for the model selected by Ailovanta

No OpenAI, Anthropic, Gemini, hosted database, hosted vector store, or paid model API is required.

## Open an existing repository

### macOS / Linux

```bash
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
bash start-local.sh --project /absolute/path/to/your/repo
```

### Windows PowerShell

```powershell
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
.\start-local.ps1 --project C:\absolute\path\to\your\repo
```

The first run will:

1. create `.venv` and install the lean local dependencies;
2. detect RAM/GPU/VRAM;
3. start or reuse local Ollama;
4. choose a practical coding model and context window;
5. ask before a missing model is downloaded;
6. record the actual local model digest;
7. import supported source files into an Ailovanta working copy;
8. open `127.0.0.1:8765` in the browser.

The original repository is **not** changed when the AI proposes or applies changes inside the Ailovanta working copy.

## Daily workflow

```text
open linked repo
    -> ask Auto / Frontend / Backend / Repair
    -> repository-aware context selection
    -> first local coding pass
    -> local self-review pass when it fits the context window
    -> static validation
    -> review complete file changes
    -> Apply selected changes to the Ailovanta copy
    -> inspect Diff
    -> Sync to disk
```

`Sync to disk` is explicit. Before writing to the original repository Ailovanta:

- checks that every touched source file still matches the baseline imported from disk;
- aborts the whole sync if a file changed in another editor/process;
- stores backups of overwritten/deleted source files under the Ailovanta runtime project directory;
- writes the accepted batch;
- advances the baseline only after success.

If Ailovanta is reopened with the same `--project` path:

- a clean working copy refreshes from the current disk contents;
- a working copy with unsynced changes is preserved instead of overwritten.

## Hardware selection

The bootstrap policy intentionally leaves memory for KV cache and the coding workspace. Approximate defaults:

```text
28GB+ NVIDIA VRAM + 32GB+ RAM -> qwen3-coder:30b, 32K context
22GB+ NVIDIA VRAM + 32GB+ RAM -> qwen3-coder:30b, 16K context
14GB+ NVIDIA VRAM             -> qwen2.5-coder:14b, 24K context
8GB+ NVIDIA VRAM              -> qwen2.5-coder:7b, 16K context
Apple Silicon 48GB+           -> qwen3-coder:30b, 32K context
Apple Silicon 24GB+           -> qwen2.5-coder:14b, 24K context
16GB+ system RAM              -> qwen2.5-coder:7b, 12K context
lower-memory fallback         -> qwen2.5-coder:3b, 8K context
```

Override when desired:

```bash
bash start-local.sh --project /repo --model qwen2.5-coder:14b --context 16384
```

## Model integrity lock

Ailovanta records the digest reported by the local Ollama model on first use. If the same model tag later points at different bytes, Ailovanta stops instead of silently accepting a quality change.

After an intentional model update, explicitly accept the new digest:

```bash
bash start-local.sh --project /repo --accept-model-change
```

The local UI also shows the model and shortened digest/integrity state.

## Privacy boundary

Private-local mode binds to loopback. Project files, prompts, and inference output do not need to be sent to the public Ailovanta control plane.

Community compute is a different, explicit opt-in mode. Community workers accept only `public` or `synthetic` coding-inference workloads. Private project payloads are rejected by both scheduler policy and worker policy.

## Public control plane

The public domain does not need a model GPU or Ollama:

```bash
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
make control-public AILOVANTA_DOMAIN=code.example.com
```

The control-plane compose runs FastAPI + SQLite + Caddy. Private coding project routes are not registered in `control-plane` mode.

## Current model status

The product workflow is real and usable now, but the final proprietary three-stream Ailovanta checkpoint has **not** been trained yet. Current local runtime weights are open bootstrap coding models selected for the user's hardware.

The owned-model target remains:

```text
Frontend specialist
+ Backend/repository specialist
+ Repair/debug specialist
    -> same-base expert checkpoints
    -> unification
    -> one Ailovanta-owned coding checkpoint
```

When that checkpoint exists it can replace the bootstrap model without changing the local product workflow.
