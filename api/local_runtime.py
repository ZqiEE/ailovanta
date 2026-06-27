from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalRuntime:
    def __init__(self) -> None:
        self.loaded: dict[str, Any] = {}

    def load(self, model_key: str, location: str) -> dict[str, Any]:
        path = Path(location)
        record = {"model_key": model_key, "location": str(path), "backend": "metadata", "ready": path.exists()}
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # type: ignore
            if path.exists() and any((path / item).exists() for item in ["config.json", "adapter_config.json"]):
                tokenizer = AutoTokenizer.from_pretrained(str(path))
                model = AutoModelForCausalLM.from_pretrained(str(path))
                record["pipe"] = pipeline("text-generation", model=model, tokenizer=tokenizer)
                record["backend"] = "transformers"
                record["ready"] = True
        except Exception as exc:
            record["message"] = str(exc)
        self.loaded[model_key] = record
        return self.public(record)

    def generate(self, model_key: str, prompt: str, max_new_tokens: int = 128) -> dict[str, Any]:
        record = self.loaded.get(model_key)
        if not record:
            return {"ok": False, "reason": "model not loaded", "model_key": model_key}
        if record.get("backend") == "transformers" and record.get("pipe") is not None:
            output = record["pipe"](prompt, max_new_tokens=max_new_tokens, do_sample=False)
            text = output[0].get("generated_text", "") if output else ""
            return {"ok": True, "model_key": model_key, "backend": "transformers", "text": text}
        metadata = self.read_metadata(record["location"])
        text = "Ailovanta runtime fallback: model metadata loaded, install optional model deps and publish real weights for generation."
        return {"ok": True, "model_key": model_key, "backend": "metadata", "text": text, "metadata": metadata}

    def list(self) -> list[dict[str, Any]]:
        return [self.public(item) for item in self.loaded.values()]

    @staticmethod
    def read_metadata(location: str) -> dict[str, Any]:
        path = Path(location)
        for name in ["output.json", "artifact.json", "merged.json"]:
            item = path / name
            if item.exists():
                try:
                    return json.loads(item.read_text(encoding="utf-8"))
                except Exception:
                    return {}
        return {}

    @staticmethod
    def public(record: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in record.items() if key != "pipe"}
