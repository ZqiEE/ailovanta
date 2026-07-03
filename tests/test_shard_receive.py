import base64
from pathlib import Path

from api.shard_receive import receive_shard, sha256_bytes


def test_receive_shard_accepts_matching_hash(tmp_path: Path) -> None:
    data = b"hello shard"
    result = receive_shard(
        artifact_hash="sha256:artifact",
        shard_index=0,
        shard_hash=sha256_bytes(data),
        data_base64=base64.b64encode(data).decode("utf-8"),
        root=tmp_path,
    )
    assert result["ok"] is True
    assert Path(result["stored_path"]).read_bytes() == data


def test_receive_shard_rejects_bad_hash(tmp_path: Path) -> None:
    data = b"hello shard"
    result = receive_shard(
        artifact_hash="sha256:artifact",
        shard_index=0,
        shard_hash="sha256:bad",
        data_base64=base64.b64encode(data).decode("utf-8"),
        root=tmp_path,
    )
    assert result["ok"] is False
    assert result["stored_path"] is None
