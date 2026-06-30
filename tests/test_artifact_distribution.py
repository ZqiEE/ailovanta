from pathlib import Path

from api.artifact_distribution import distribution_metadata, prepare_local_artifact_distribution


def test_prepare_local_artifact_distribution(tmp_path: Path) -> None:
    artifact_path = tmp_path / "model.bin"
    artifact_path.write_bytes(b"model-bytes")
    artifact = {
        "artifact_id": "artifact_local_1",
        "artifact_hash": "sha256:not-the-storage-hash",
        "checkpoint_uri": "file://" + str(artifact_path),
    }

    distribution = prepare_local_artifact_distribution(
        artifact,
        "file://" + str(artifact_path),
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
        storage_node_id="storage-local-1",
    )

    assert distribution is not None
    assert distribution["schema_version"] == "ailovanta.artifact_distribution.v1"
    assert distribution["manifest_hash"].startswith("sha256:")
    assert distribution["storage_artifact_hash"].startswith("sha256:")
    assert distribution["hash_matches_model_artifact"] is False
    assert Path(distribution["manifest_uri"].removeprefix("file://")).exists()
    assert distribution["replica_status"]["artifact_count"] == 1
    assert "book" not in distribution_metadata(distribution)
