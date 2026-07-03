from api.artifact_placement import plan_shard_placement, verify_placement


class FakeRuntimeStore:
    def list_runtimes(self):
        return [
            {"runtime_id": "rt-a", "node_id": "node-a", "region": "lan", "pool": "trusted_runtime_pool", "status": "online"},
            {"runtime_id": "rt-b", "node_id": "node-b", "region": "lan", "pool": "trusted_runtime_pool", "status": "online"},
        ]


def test_plan_shard_placement_replicates_across_nodes() -> None:
    manifest = {
        "artifact_hash": "sha256:abc",
        "shards": [
            {"index": 0, "hash": "sha256:s0", "size_bytes": 10},
            {"index": 1, "hash": "sha256:s1", "size_bytes": 20},
        ],
    }
    plan = plan_shard_placement(manifest, replication=2, runtime_store=FakeRuntimeStore())
    assert plan["shard_count"] == 2
    assert len(plan["assignments"][0]["nodes"]) == 2
    assert verify_placement(plan)["ok"] is True
