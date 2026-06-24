from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.foundation_result_import import import_foundation_result
from api.runtime_store import RuntimeStore


def test_import_foundation_result_registers_runtime_and_chain(tmp_path) -> None:
    result = import_foundation_result(
        {
            "plan": {
                "plan_id": "foundation_plan_1",
                "plan_hash": "sha256:plan1",
                "model": {"model_id": "ailovanta-owned", "target_version": "candidate"},
            },
            "artifact": {
                "schema_version": "ailovanta.foundation_artifact.v1",
                "artifact_id": "foundation_artifact_1",
                "model_id": "ailovanta-owned",
                "version": "candidate",
                "source_plan_id": "foundation_plan_1",
                "checkpoint_uri": "artifact://checkpoint",
                "artifact_hash": "sha256:artifact1",
                "promotion_status": "candidate",
            },
        },
        core_results=CoreResultStore(tmp_path / "core.sqlite3"),
        runtime_store=RuntimeStore(tmp_path / "runtime.sqlite3"),
        chain_registry=ChainRegistry(tmp_path / "chain.sqlite3"),
    )

    assert result["runtime_model"]["model_id"] == "ailovanta-owned"
    assert result["runtime_model"]["manifest_hash"] == "sha256:artifact1"
    assert result["chain_event"]["artifact_hash"] == "sha256:artifact1"
