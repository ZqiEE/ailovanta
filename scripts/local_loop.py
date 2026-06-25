from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from time import time

from api.final_report import report
from api.g2 import run_gate
from api.node_proof import attach_proof
from api.node_trust import NodeTrustStore
from api.parcel_store import ParcelStore
from api.ra2 import apply2


def sha(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_plan(path: Path) -> dict:
    plan = {
        "schema_version": "ailovanta.foundation_plan.v1",
        "plan_id": "foundation_plan_local_demo",
        "plan_hash": sha("foundation_plan_local_demo"),
        "model": {"model_id": "ailovanta-owned", "target_version": "candidate", "parameter_count_b": 1.0, "context_length": 8192},
        "nodes": [{"node_id": "node-local-1", "gpu_memory_gb": 24.0, "gpu_count": 1, "trust_score": 0.95, "region": "local"}],
        "estimated_total_tokens": 128,
        "max_steps": 1,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def write_outbox(secret: str) -> dict:
    payload = {
        "id": "local_demo_out_1",
        "task_id": "local_demo_task_1",
        "node_id": "node-local-1",
        "checkpoint_uri": "artifact://foundation_plan_local_demo/node-local-1",
        "checkpoint_hash": sha("local-demo-checkpoint"),
        "token_count": 128,
        "train_loss": 0.2,
        "eval_loss": 0.2,
        "created_at": round(time(), 3),
    }
    signed = attach_proof(payload, "node-local-1", secret)
    ParcelStore().put_outbox(signed)
    return signed


def run_json(command: list[str], cwd: Path) -> dict:
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, *command], cwd=cwd, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Ailovanta loop demo")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--root", default="runtime_data/local_loop")
    parser.add_argument("--secret", default="local-demo-secret")
    args = parser.parse_args()

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / "foundation_plan.json"
    set_path = root / "checkpoint_set.json"
    result_path = root / "foundation_result.json"
    receipts_path = Path("runtime_data/parcels/checkpoint_receipts.json")
    core = Path(args.core_path).resolve()

    NodeTrustStore().register("node-local-1", args.secret, trust_score=0.95, metadata={"demo": True})
    os.environ["AILOVANTA_NODE_SECRETS_JSON"] = json.dumps({"node-local-1": args.secret})
    plan = write_plan(plan_path)
    signed = write_outbox(args.secret)

    from api.parcel_receipts import export_receipts

    receipts = export_receipts(output_path=receipts_path, require_proof=True)
    checkpoint_set = run_json(["scripts/finalize_receipts.py", str(plan_path.resolve()), str(receipts_path.resolve()), "--output", str(set_path.resolve())], cwd=core)
    make_script = core / "scripts" / "make_artifact_v2.py"
    if not make_script.exists():
        make_script = core / "scripts" / "make_artifact.py"
    artifact = run_json([str(make_script), str(plan_path.resolve()), str(set_path.resolve()), "--output", str(result_path.resolve())], cwd=core)
    gate = run_gate(result_path, core_path=core, work_dir=root / "gate")
    applied = apply2(result_path)
    final = report(result_path)
    output = {"ok": bool(final.get("ok")), "plan": plan, "signed": signed, "receipts": receipts, "checkpoint_set": checkpoint_set, "artifact": artifact, "gate": gate, "apply": applied, "final": final}
    out_path = root / "local_loop_report.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": output["ok"], "report_path": str(out_path), "final": final}, ensure_ascii=False, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
