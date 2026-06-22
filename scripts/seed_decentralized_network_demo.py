from __future__ import annotations

import json

from api.content_addressing import hash_object
from api.contribution_ledger import ContributionLedger
from api.decentralized_identity import create_ledger_identity, identity_hash
from api.model_commit_registry import ModelCommitRegistry
from api.network_validator import NetworkValidator
from api.task_proof import build_task_proof
from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner


def main() -> None:
    node_id = "node_decentralized_demo"
    identity = create_ledger_identity(node_id, public_label="demo-ai-node")
    runner = JobRunner()
    job = {"id": "job_decentralized_eval", "type": "evaluation", "payload": {"samples": 2}}
    result = runner.run(job)
    report = build_execution_report(node_id, job, result)
    proof = build_task_proof(report)
    validation = NetworkValidator().score_proof(proof, report)

    ledger = ContributionLedger()
    identity_event = ledger.append(node_id, "identity", identity_hash(identity), 1.0, 1.0, {"address": identity["ledger_address"]})
    proof_event = ledger.append(node_id, "task_proof", proof["report_hash"], validation["score"], validation["credits"], {"proof_id": proof["proof_id"], "passed": validation["passed"]})

    model_hash = hash_object({"model": "demo-private-model", "source": proof["proof_id"]})
    model_commit = ModelCommitRegistry().register("demo-private-model", "v0.1", model_hash, proof["proof_id"], validation["score"], {"node_id": node_id})

    output = {
        "identity": identity,
        "report": report,
        "proof": proof,
        "validation": validation,
        "identity_event": identity_event,
        "proof_event": proof_event,
        "model_commit": model_commit,
        "ledger_summary": ledger.network_summary(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
