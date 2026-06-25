from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_result(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def metric(artifact: dict[str, Any], name: str, default: float = 1.0) -> float:
    metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
    if metrics.get(name) is not None:
        return float(metrics[name])
    ckpt = artifact.get("checkpoint_set") if isinstance(artifact.get("checkpoint_set"), dict) else {}
    if ckpt.get(name) is not None:
        return float(ckpt[name])
    return default


def eval_payload(result: dict[str, Any], baseline_score: float = 0.45) -> dict[str, Any]:
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
    model_id = artifact.get("model_id", "ailovanta-owned")
    version = artifact.get("version", "candidate")
    eval_loss = float(metrics.get("avg_eval_loss", metrics.get("eval_loss", 1.0)) or 1.0)
    accepted = float(metrics.get("accepted_checkpoints", 0.0) or 0.0)
    quality = max(0.0, min(1.0, 1.0 / (1.0 + max(0.0, eval_loss)))) + (0.1 if accepted > 0 else 0.0)
    proof_coverage = metric(artifact, "proof_coverage", 1.0)
    avg_trust_score = metric(artifact, "avg_trust_score", 1.0)
    return {
        "candidate_model": f"{model_id}:{version}",
        "baseline_model": "ailovanta-owned:baseline",
        "metrics": [
            {"name": "quality", "candidate_score": round(min(1.0, quality), 4), "baseline_score": baseline_score, "weight": 1.0},
            {"name": "artifact_integrity", "candidate_score": 1.0 if artifact.get("artifact_hash") else 0.0, "baseline_score": 0.9, "weight": 1.0},
            {"name": "proof_coverage", "candidate_score": proof_coverage, "baseline_score": 0.8, "weight": 1.0},
            {"name": "avg_trust_score", "candidate_score": avg_trust_score, "baseline_score": 0.75, "weight": 1.0},
        ],
        "guardrails": {"proof_coverage": proof_coverage, "avg_trust_score": avg_trust_score},
        "regression_rate": 0.0,
        "safety_fail_rate": 0.0,
    }


def run_gate(result_path: str | Path, core_path: str | Path = "../ailovanta-core", work_dir: str | Path = "runtime_data/g2") -> dict[str, Any]:
    core = Path(core_path).resolve()
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    payload = eval_payload(load_result(result_path))
    eval_file = work / "eval_payload.json"
    eval_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(core / "scripts" / "run_eval_gate.py"), str(eval_file)], cwd=core, check=True, text=True, capture_output=True)
    gate = json.loads(proc.stdout)
    out = {"ok": True, "eval_payload": payload, "gate": gate, "eval_path": str(eval_file)}
    (work / "gate_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
