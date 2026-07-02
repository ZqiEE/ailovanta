from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import FastAPI
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore

app = FastAPI(title="Ailovanta Worker", version="0.3.1")

_loaded: dict[str, dict] = {}


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    policy_mode: str = "open_research"
    runtime_id: str
    node_id: str
    model_manifest_hash: str
    max_new_tokens: int = 128


def ref_path(value: str | None) -> Path | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "file":
        raw = unquote(parsed.path)
        if len(raw) >= 3 and raw[0] == "/" and raw[2] == ":":
            raw = raw[1:]
        return Path(raw)
    if parsed.scheme == "":
        return Path(value)
    return None


def read_checkpoint(path: Path | None) -> dict:
    if not path or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_model_dir(checkpoint: dict, checkpoint_path: Path | None) -> str | None:
    raw = checkpoint.get("model_dir")
    if not raw:
        return None
    model_path = Path(str(raw))
    if not model_path.is_absolute() and checkpoint_path is not None:
        model_path = checkpoint_path.parent / model_path
    return str(model_path.resolve())


def looks_loadable(path: Path) -> bool:
    return path.is_dir() and (path / "config.json").exists()


def generate_local(model_dir: str | None, prompt: str, max_new_tokens: int) -> dict:
    if not model_dir:
        return {"ok": False, "reason": "missing_model_dir"}
    path = Path(model_dir)
    if not looks_loadable(path):
        return {"ok": False, "reason": "model_dir_not_loadable", "model_dir": str(path)}
    key = str(path.resolve())
    try:
        if key not in _loaded:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
            import torch  # type: ignore

            tokenizer = AutoTokenizer.from_pretrained(key)
            model = AutoModelForCausalLM.from_pretrained(key)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(device)
            model.eval()
            _loaded[key] = {"model": model, "tokenizer": tokenizer, "device": device, "torch": torch}
        loaded = _loaded[key]
        tokenizer = loaded["tokenizer"]
        model = loaded["model"]
        device = loaded["device"]
        torch = loaded["torch"]
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {name: value.to(device) for name, value in inputs.items()}
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=getattr(tokenizer, "eos_token_id", None))
        text = tokenizer.decode(out[0], skip_special_tokens=True)
        return {"ok": True, "answer": text, "backend": "transformers-local", "model_dir": key, "device": device}
    except Exception as exc:
        return {"ok": False, "reason": "local_generation_failed", "error": str(exc), "model_dir": key}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    model_key = body.model_id + ":" + body.version
    binding = ArtifactBindingStore().latest_for_model(model_key, active_only=True)
    backend_kind = binding.get("backend_kind") if binding else None
    backend_ref = binding.get("backend_ref") if binding else None
    path = ref_path(backend_ref)
    path_ready = bool(path and path.exists())
    checkpoint = read_checkpoint(path)
    model_dir = resolve_model_dir(checkpoint, path)
    gen = generate_local(model_dir, body.prompt, body.max_new_tokens)
    answer = gen.get("answer") if gen.get("ok") else "Ailovanta worker routed request for " + model_key
    return {
        "answer": answer,
        "source": gen.get("backend") if gen.get("ok") else "ailovanta-worker",
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
        "policy_mode": body.policy_mode,
        "artifact_binding_found": binding is not None,
        "binding_id": binding.get("binding_id") if binding else None,
        "backend_kind": backend_kind,
        "backend_ref": backend_ref,
        "artifact_path_ready": path_ready,
        "artifact_path": str(path) if path else None,
        "checkpoint_backend": checkpoint.get("backend"),
        "checkpoint_model_dir": model_dir,
        "checkpoint_base_model": checkpoint.get("base_model"),
        "generation": gen,
    }
