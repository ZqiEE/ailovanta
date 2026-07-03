from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from api.continuous_training_ledger import record_training_batch, sync_ledger_with_jobs, write_limited_sources
from api.github_code_ingest import ingest_sources


def post_json(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        server.rstrip("/") + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(server: str, path: str) -> dict[str, Any]:
    request = urllib.request.Request(server.rstrip("/") + path, method="GET")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def run_autonomous_source_training_cycle(
    server: str = "http://127.0.0.1:8000",
    sources_path: str | Path = "runtime_data/github_code_sources.json",
    work_root: str | Path = "runtime_data/autonomous_source_training",
    discover: bool = True,
    fetch: bool = True,
    max_sources: int = 3,
    max_records: int = 512,
    corpus_mode: str = "mixed",
    max_steps: int = 16,
    base_model: str = "sshleifer/tiny-gpt2",
    training_backend: str = "auto",
    require_gpu: bool = True,
    allow_lightweight_fallback: bool = False,
    frontier_path: str | Path = "runtime_data/github_source_frontier.json",
    max_discovery_queries: int = 5,
    ledger_path: str | Path = "runtime_data/continuous_training_ledger.json",
) -> dict[str, Any]:
    root = Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    sources = Path(sources_path)

    discovery = discover_sources_if_needed(sources, enabled=discover, frontier_path=frontier_path, max_queries=max_discovery_queries)
    scheduler_sync = sync_training_ledger_from_server(server, ledger_path)
    selection = limit_sources(sources, root / "sources_limited.json", max_sources, ledger_path=ledger_path, corpus_mode=corpus_mode)
    limited_sources = Path(str(selection["output"]))
    if not selection["selected"]:
        return {
            "ok": False,
            "stage": "no_new_sources",
            "discovery": discovery,
            "scheduler_sync": scheduler_sync,
            "selection": selection,
        }
    corpus_path = root / "code_corpus.jsonl"
    ingest = ingest_sources(
        limited_sources,
        target_root=root / "source_repos",
        corpus_output=corpus_path,
        rights_path=root / "rights_proofs.json",
        jobs_path=root / "code_training_jobs.json",
        fetch=fetch,
        create_job=False,
        corpus_mode=corpus_mode,
    )
    dataset_path = root / "autonomous_training_dataset.jsonl"
    dataset = corpus_to_training_dataset(corpus_path, dataset_path, max_records=max_records)
    if dataset["records"] <= 0:
        return {
            "ok": False,
            "stage": "no_training_records",
            "discovery": discovery,
            "scheduler_sync": scheduler_sync,
            "selection": selection,
            "ingest": compact_ingest(ingest),
            "dataset": dataset,
        }

    job_payload = build_autonomous_training_job_payload(
        dataset_path=dataset_path,
        max_steps=max_steps,
        base_model=base_model,
        training_backend=training_backend,
        require_gpu=require_gpu,
        allow_lightweight_fallback=allow_lightweight_fallback,
    )
    job = post_json(
        server,
        "/training/jobs",
        job_payload,
    )
    ledger = record_training_batch(
        ledger_path,
        selected_sources=selection["selected"],
        dataset_path=dataset_path,
        dataset=dataset,
        job=job,
        ingest=ingest,
        corpus_mode=corpus_mode,
    )
    return {
        "ok": True,
        "stage": "training_job_queued",
        "server": server,
        "discovery": discovery,
        "scheduler_sync": scheduler_sync,
        "selection": selection,
        "ingest": compact_ingest(ingest),
        "dataset": dataset,
        "job": job,
        "job_payload": job_payload,
        "ledger": {"path": str(ledger_path), "sources": len(ledger.get("sources", {})), "batches": len(ledger.get("batches", {}))},
        "created_at": round(time.time(), 3),
    }


def build_autonomous_training_job_payload(
    *,
    dataset_path: str | Path,
    max_steps: int,
    base_model: str,
    training_backend: str = "auto",
    require_gpu: bool = True,
    allow_lightweight_fallback: bool = False,
) -> dict[str, Any]:
    backend = training_backend.lower().strip()
    if backend not in {"auto", "lora", "qlora", "transformers"}:
        raise ValueError("training_backend must be one of: auto, lora, qlora, transformers")
    payload: dict[str, Any] = {
        "kind": "lora_micro",
        "name": "ailovanta-auto-source",
        "dataset_uri": "file://" + str(Path(dataset_path).resolve()),
        "base_model": base_model,
        "max_steps": max_steps,
        "real": True,
        "use_transformers": True,
        "requires_gpu": require_gpu,
        "allow_lightweight_fallback": allow_lightweight_fallback,
        "priority": 100 if require_gpu else 80,
        "training_backend": backend,
        "notes": "autonomous source discovery -> ingest -> real Transformers/LoRA training job",
    }
    if backend in {"lora", "qlora"}:
        payload["peft"] = True
        payload["lora"] = True
    if backend == "qlora":
        payload["qlora"] = True
    return payload


def discover_sources_if_needed(output_path: Path, enabled: bool, frontier_path: str | Path = "runtime_data/github_source_frontier.json", max_queries: int = 5) -> dict[str, Any]:
    if output_path.exists() and not enabled:
        return {"ok": True, "enabled": False, "reason": "existing_sources", "output": str(output_path)}
    if not enabled and not output_path.exists():
        raise FileNotFoundError("sources file not found and discovery disabled: " + str(output_path))

    from api.github_source_frontier import run_frontier_discovery
    from scripts.discover_github_sources import load_manifest, save_manifest, search_repositories, source_from_repo, upsert_sources

    import os

    token = os.getenv("GITHUB_TOKEN")
    result = run_frontier_discovery(
        sources_path=output_path,
        frontier_path=frontier_path,
        search_repositories=search_repositories,
        source_from_repo=source_from_repo,
        upsert_sources=upsert_sources,
        load_manifest=load_manifest,
        save_manifest=save_manifest,
        token=token,
        max_queries=max_queries,
        pages=1,
        per_page=10,
        policy="authorized_unrestricted",
        authorization_basis="operator authorized autonomous GitHub source discovery",
    )
    return {**result, "enabled": True, "output": str(output_path)}


def sync_training_ledger_from_server(server: str, ledger_path: str | Path) -> dict[str, Any]:
    try:
        jobs = get_json(server, "/training/jobs?limit=200").get("jobs", [])
    except Exception as exc:
        return {"ok": False, "reason": type(exc).__name__, "message": str(exc), "ledger_path": str(ledger_path)}
    return sync_ledger_with_jobs(ledger_path, jobs)


def limit_sources(source_path: Path, output_path: Path, max_sources: int, ledger_path: str | Path = "runtime_data/continuous_training_ledger.json", corpus_mode: str = "mixed") -> dict[str, Any]:
    return write_limited_sources(source_path, output_path, ledger_path, max_sources=max_sources, corpus_mode=corpus_mode)


def corpus_to_training_dataset(corpus_path: str | Path, output_path: str | Path, max_records: int = 512) -> dict[str, Any]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    bytes_written = 0
    selection = _select_training_records(corpus_path, max_records=max_records)
    selected = selection["records"]
    with output.open("w", encoding="utf-8") as target:
        for item in selected:
            text = training_text_from_record(item)
            if not text:
                continue
            payload = {
                "text": text,
                "source_path": item.get("path"),
                "source_name": item.get("source_name"),
                "rights_id": item.get("rights_id"),
                "record_kind": item.get("training_record_kind"),
                "curriculum_tags": item.get("curriculum_tags") or [],
                "priority_tier": item.get("priority_tier"),
                "priority_score": item.get("priority_score"),
            }
            encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            target.write(encoded + "\n")
            records += 1
            bytes_written += len(encoded.encode("utf-8", errors="ignore"))
    return {
        "ok": records > 0,
        "output": str(output),
        "records": records,
        "bytes": bytes_written,
        "selected_tags": _selected_tag_counts(selected),
        "duplicates_skipped": selection["duplicates_skipped"],
    }


def training_text_from_record(item: dict[str, Any]) -> str:
    if item.get("training_record_kind") == "instruction":
        parts = [
            "Instruction: " + str(item.get("instruction") or "").strip(),
            "Context: " + str(item.get("context") or "").strip()[:6000],
            "Expected: " + str(item.get("expected_response") or "").strip(),
        ]
        return "\n\n".join(part for part in parts if len(part.strip()) > 12).strip()
    text = str(item.get("text") or item.get("content") or "").strip()
    if text:
        return text[:8000]
    return ""


def compact_ingest(ingest: dict[str, Any]) -> dict[str, Any]:
    keys = ["ok", "sources", "accepted_sources", "records", "bytes", "languages", "corpus_output", "corpus_mode"]
    return {key: ingest.get(key) for key in keys}


def _select_training_records(corpus_path: str | Path, *, max_records: int) -> dict[str, Any]:
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    duplicates_skipped = 0
    with Path(corpus_path).open("r", encoding="utf-8") as source:
        for index, line in enumerate(source):
            if not line.strip():
                continue
            item = json.loads(line)
            ranked.append((_record_priority(item), -index, item))
    ranked.sort(reverse=True)
    selected: list[dict[str, Any]] = []
    seen_fingerprints: set[str] = set()
    for _score, _neg_index, item in ranked:
        fingerprint = _training_record_fingerprint(item)
        if fingerprint in seen_fingerprints:
            duplicates_skipped += 1
            continue
        seen_fingerprints.add(fingerprint)
        selected.append(dict(item))
        if len(selected) >= max_records:
            break
    return {"records": selected, "duplicates_skipped": duplicates_skipped}


def _record_priority(item: dict[str, Any]) -> int:
    tags = {str(tag) for tag in item.get("curriculum_tags", []) or []}
    score = int(item.get("priority_score") or 0)
    if item.get("training_record_kind") == "instruction":
        score += 160
    if "algorithmic_core" in tags:
        score += 80
    if "syntax_foundation" in tags:
        score += 60
    if "test_driven_sample" in tags:
        score += 50
    if "api_usage" in tags:
        score += 40
    return score


def _selected_tag_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for tag in item.get("curriculum_tags", []) or []:
            key = str(tag)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _training_record_fingerprint(item: dict[str, Any]) -> str:
    text = training_text_from_record(item)
    normalized = " ".join(text.split())
    record_kind = str(item.get("training_record_kind") or "")
    payload = json.dumps(
        {
            "record_kind": record_kind,
            "text": normalized,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
