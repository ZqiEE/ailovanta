from api.learning_foundation import build_job_from_pack


def test_build_job_from_pack() -> None:
    pack = {
        "pack_id": "pack_test",
        "pack_hash": "sha256:test",
        "sft": [{"instruction": "hello", "output": "world", "score": 0.9, "sample_id": "s1"}],
        "dpo": [],
    }
    job = build_job_from_pack(pack, target_version="candidate")
    assert job["schema_version"] == "ailovanta.foundation_job.v1"
    assert job["stage"] == "sft"
    assert job["dataset_shards"]
