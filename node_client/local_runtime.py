from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import webbrowser

import httpx

from node_client.model_profile import LocalModelProfile, recommend_local_model


OLLAMA_URL = "http://127.0.0.1:11434"


def _ollama_models() -> set[str] | None:
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
        response.raise_for_status()
        return {str(row.get("name") or "") for row in response.json().get("models", [])}
    except Exception:
        return None


def _start_ollama() -> subprocess.Popen | None:
    if not shutil.which("ollama"):
        return None
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    for _ in range(30):
        if _ollama_models() is not None:
            return process
        time.sleep(0.5)
    return process


def _present(models: set[str], model: str) -> bool:
    wanted_base = model.split(":", 1)[0]
    return model in models or any(name.split(":", 1)[0] == wanted_base for name in models)


def _pull(model: str) -> None:
    if not shutil.which("ollama"):
        raise RuntimeError("Ollama CLI is not installed. Install Ollama first, then rerun Ailovanta Local.")
    print(f"Downloading local model {model}. This is a one-time local download.")
    subprocess.run(["ollama", "pull", model], check=True)


def _choose_profile(model_override: str | None, context_override: int | None) -> LocalModelProfile:
    profile = recommend_local_model()
    if model_override or context_override:
        profile = LocalModelProfile(
            model=model_override or profile.model,
            context_length=context_override or profile.context_length,
            reason="operator override" if model_override or context_override else profile.reason,
            gpu_name=profile.gpu_name,
            gpu_memory_gb=profile.gpu_memory_gb,
            system_memory_gb=profile.system_memory_gb,
        )
    return profile


def _confirm_pull(model: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        return False
    answer = input(f"Model {model} is not installed. Download it now? [Y/n] ").strip().lower()
    return answer in {"", "y", "yes"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Ailovanta Coding privately on this computer using this computer's GPU/CPU."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Keep 127.0.0.1 for private local use.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default=None, help="Override the hardware-selected Ollama model.")
    parser.add_argument("--context", type=int, default=None, help="Override model context length.")
    parser.add_argument("--yes", action="store_true", help="Download the recommended model without prompting.")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Ailovanta Local binds to loopback by default. Use a reverse proxy only if you understand the exposure risk.")

    profile = _choose_profile(args.model, args.context)
    print("Ailovanta Local")
    print("- private project files stay on this computer")
    print("- inference uses this computer's local Ollama runtime")
    print("- no OpenAI/Anthropic/Google model API is required")
    print(f"- selected model: {profile.model}")
    print(f"- context: {profile.context_length}")
    print(f"- hardware decision: {profile.reason}")

    models = _ollama_models()
    started = None
    if models is None:
        started = _start_ollama()
        models = _ollama_models()
    if models is None:
        raise SystemExit("Ollama is not reachable and could not be started. Install/start Ollama, then rerun this command.")

    if not _present(models, profile.model):
        if not _confirm_pull(profile.model, args.yes):
            raise SystemExit(f"Required local model is missing: {profile.model}")
        _pull(profile.model)

    # Set runtime configuration before importing the FastAPI application.
    os.environ["OLLAMA_BASE_URL"] = OLLAMA_URL
    os.environ["OLLAMA_MODEL"] = profile.model
    os.environ["OLLAMA_CONTEXT_LENGTH"] = str(profile.context_length)
    os.environ["AILOVANTA_RUNTIME_MODE"] = "private-local"
    os.environ["AILOVANTA_ZERO_CASH_MODE"] = "true"
    os.environ["AILOVANTA_PROJECT_ROOT"] = os.getenv(
        "AILOVANTA_PROJECT_ROOT", "runtime_data/local_coding_projects"
    )

    import uvicorn

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        # Give Uvicorn a moment to bind before the browser opens.
        import threading

        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run("api.product_app:app", host=args.host, port=args.port, log_level="info")
    finally:
        if started is not None and started.poll() is None:
            # We only stop a daemon that this launcher started itself.
            started.terminate()


if __name__ == "__main__":
    main()
