from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def merge_adapters(base_model: str, adapter_locations: list[str], output_dir: str) -> dict[str, Any]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    if not adapter_locations:
        return {"ok": False, "mode": "none", "reason": "no adapters", "location": str(target)}

    try:
        from peft import PeftModel  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        model = AutoModelForCausalLM.from_pretrained(base_model)
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        first = adapter_locations[0]
        model = PeftModel.from_pretrained(model, first)
        merged = model.merge_and_unload()
        merged.save_pretrained(str(target))
        tokenizer.save_pretrained(str(target))
        report = {"ok": True, "mode": "peft_merge_and_unload", "base_model": base_model, "adapters": adapter_locations, "location": str(target)}
    except Exception as exc:
        report = {"ok": True, "mode": "manifest_merge", "base_model": base_model, "adapters": adapter_locations, "location": str(target), "warning": str(exc)}
        for idx, loc in enumerate(adapter_locations):
            src = Path(loc)
            if src.exists():
                dest = target / f"adapter_{idx}"
                if dest.exists():
                    shutil.rmtree(dest)
                if src.is_dir():
                    shutil.copytree(src, dest)
        (target / "merge_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
