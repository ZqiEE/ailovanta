from __future__ import annotations

import json
from pathlib import Path


def transformers_model_load_ref(model_path: Path) -> str:
    adapter_base = peft_adapter_base_model_ref(model_path)
    return adapter_base or str(model_path)


def peft_adapter_base_model_ref(model_path: Path) -> str | None:
    output_path = model_path / "output.json"
    if output_path.exists():
        try:
            output = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception:
            output = {}
        backend = str(((output.get("metrics") or {}) if isinstance(output.get("metrics"), dict) else {}).get("backend") or "")
        if backend in {"lora", "qlora"} and output.get("base_model"):
            return str(output["base_model"])

    adapter_config = model_path / "adapter_config.json"
    if not adapter_config.exists():
        return None
    try:
        config = json.loads(adapter_config.read_text(encoding="utf-8"))
    except Exception:
        return None
    base_ref = config.get("base_model_name_or_path") or config.get("base_model")
    return str(base_ref) if base_ref else None
