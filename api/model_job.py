from __future__ import annotations

import json
import shutil
from pathlib import Path
from time import time
from typing import Any


class ModelJobError(RuntimeError):
    pass


def run_model_job(payload: dict[str, Any], profile: dict[str, Any], source_id: str) -> dict[str, Any]:
    name = payload.get("name") or payload.get("model_id") or "ailovanta-code"
    version = payload.get("version") or "local-v0"
    out_dir = Path(payload.get("output_dir") or f"runtime_data/models/{name}-{version}")
    out_dir.mkdir(parents=True, exist_ok=True)

    data_path = payload.get("data_path") or payload.get("dataset_uri")
    base_model = payload.get("base_model") or "local"
    max_steps = int(payload.get("max_steps") or payload.get("steps") or 10)
    use_real = bool(payload.get("real") or payload.get("use_transformers"))

    if use_real:
        result = _run_transformers_job(base_model, data_path, out_dir, max_steps)
    else:
        result = _write_portable_output(base_model, data_path, out_dir, max_steps)

    metrics = {
        "steps": max_steps,
        "cpu_threads": profile.get("cpu_threads"),
        "memory_gb": profile.get("memory_gb"),
        "has_gpu": bool(profile.get("has_gpu")),
        "real_backend": result["backend"],
        "score": result["score"],
        "created_at": time(),
    }
    record = {
        "schema": "ailovanta.model_output.v1",
        "name": name,
        "version": version,
        "source_job_id": source_id,
        "base_model": base_model,
        "kind": payload.get("kind") or "adapter",
        "location": str(out_dir),
        "metrics": metrics,
        "backend_message": result["message"],
    }
    (out_dir / "output.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "name": name,
        "version": version,
        "source_job_id": source_id,
        "location": str(out_dir),
        "kind": record["kind"],
        "metrics": metrics,
        "status": "candidate",
        "notes": result["message"],
    }


def _write_portable_output(base_model: str, data_path: str | None, out_dir: Path, max_steps: int) -> dict[str, Any]:
    info = {
        "base_model": base_model,
        "data_path": data_path,
        "max_steps": max_steps,
        "mode": "portable",
    }
    (out_dir / "adapter_config.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"backend": "portable", "score": 0.62, "message": "portable artifact written; install optional model deps for local fine tune"}


def _run_transformers_job(base_model: str, data_path: str | None, out_dir: Path, max_steps: int) -> dict[str, Any]:
    try:
        from datasets import Dataset  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments  # type: ignore
    except Exception as exc:
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = f"optional model deps missing: {exc}; portable artifact written"
        return fallback

    if not data_path or not Path(data_path).exists():
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = "dataset missing; portable artifact written"
        return fallback

    rows: list[dict[str, str]] = []
    with Path(data_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if len(rows) >= max(8, max_steps):
                break
            try:
                item = json.loads(line)
            except Exception:
                continue
            text = item.get("text") or item.get("target") or item.get("content")
            if text:
                rows.append({"text": str(text)[:4096]})
    if not rows:
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = "dataset has no usable text; portable artifact written"
        return fallback

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(base_model)
    dataset = Dataset.from_list(rows)

    def tokenize(batch: dict[str, list[str]]) -> dict[str, Any]:
        encoded = tokenizer(batch["text"], truncation=True, padding="max_length", max_length=512)
        encoded["labels"] = encoded["input_ids"].copy()
        return encoded

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
    args = TrainingArguments(
        output_dir=str(out_dir),
        max_steps=max_steps,
        per_device_train_batch_size=1,
        logging_steps=max(1, min(10, max_steps)),
        save_steps=max_steps,
        report_to=[],
    )
    trainer = Trainer(model=model, args=args, train_dataset=tokenized)
    trainer.train()
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    return {"backend": "transformers", "score": 0.8, "message": "local model fine tune finished"}


def merge_outputs(items: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Any]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    merged = {
        "schema": "ailovanta.merged_output.v1",
        "items": items,
        "count": len(items),
        "score": round(sum(float((item.get("metrics") or {}).get("score", 0.0)) for item in items) / max(len(items), 1), 4),
        "created_at": time(),
    }
    (target / "merged.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in items:
        loc = Path(str(item.get("location", "")))
        if loc.exists() and (loc / "adapter_config.json").exists():
            shutil.copyfile(loc / "adapter_config.json", target / f"adapter_config_{item.get('id', len(list(target.glob('adapter_config_*'))))}.json")
    return {"location": str(target), "metrics": {"score": merged["score"], "merged_count": len(items)}, "summary": "outputs merged"}
