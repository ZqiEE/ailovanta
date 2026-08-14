from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from typing import Any

import httpx

from api.model_lock import ModelLockStore
from node_client.model_profile import LocalModelProfile, recommend_local_model


OLLAMA_URL = "http://127.0.0.1:11434"


def _ollama_catalog() -> list[dict[str, Any]] | None:
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
        response.raise_for_status()
        return [row for row in response.json().get("models", []) if isinstance(row, dict)]
    except Exception:
        return None


def _ollama_models() -> set[str] | None:
    rows = _ollama_catalog()
    if rows is None:
        return None
    return {str(row.get("name") or "") for row in rows}


def _name_matches(installed: str, wanted: str) -> bool:
    if ":" in wanted:
        return installed == wanted
    return installed.split(":", 1)[0] == wanted


def _model_digest(model: str) -> str | None:
    rows = _ollama_catalog()
    if rows is None:
        return None
    selected = next(
        (row for row in rows if _name_matches(str(row.get("name") or ""), model)),
        None,
    )
    digest = str(selected.get("digest") or "") if selected else ""
    return digest or None


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
    return any(_name_matches(name, model) for name in models)


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


def _verify_model_integrity(model: str, accept_change: bool) -> dict[str, Any]:
    digest = _model_digest(model)
    store = ModelLockStore()
    state = store.ensure(model, digest, accept_change=accept_change)
    if state.get("status") == "mismatch":
        expected = state.get("expected_digest")
        actual = state.get("actual_digest")
        raise SystemExit(
            "Local model digest changed for "
            + model
            + ".\nExpected: "
            + str(expected)
            + "\nActual:   "
            + str(actual)
            + "\nAilovanta stopped instead of silently changing model quality. "
            "If you intentionally updated this model, rerun with --accept-model-change."
        )
    return state


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Ailovanta Coding privately on this computer using this computer's GPU/CPU."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Keep 127.0.0.1 for private local use.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default=None, help="Override the hardware-selected Ollama model.")
    parser.add_argument("--context", type=int, default=None, help="Override model context length.")
    parser.add_argument("--yes", action="store_true", help="Download the recommended model without prompting.")
    parser.add_argument(
        "--accept-model-change",
        action="store_true",
        help="Explicitly replace the saved digest lock after an intentional local model update.",
    )
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

    integrity = _verify_model_integrity(profile.model, args.accept_model_change)
    if integrity.get("actual_digest"):
        print(f"- model digest: {integrity['actual_digest']}")
        print(f"- model integrity: {integrity.get('status')}")
    else:
        print("- model integrity: digest unavailable from local runtime")

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
        import threading

        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run("api.product_app:app", host=args.host, port=args.port, log_level="info")
    finally:
        if started is not None and started.poll() is None:
            started.terminate()


if __name__ == "__main__":
    main()
