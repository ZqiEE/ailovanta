from pathlib import Path

from api.artifact_shards import build_file_shards, verify_shards


def test_build_file_shards_and_verify(tmp_path: Path) -> None:
    source = tmp_path / "model.bin"
    source.write_bytes(b"abcdef" * 100)
    result = build_file_shards(source, tmp_path / "shards", chunk_size=64)
    manifest = result["manifest"]
    assert manifest["shard_count"] > 1
    check = verify_shards(manifest)
    assert check["ok"] is True
    assert check["total_bytes"] == source.stat().st_size
