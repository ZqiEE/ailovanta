from node_client.cap import Accel, Cap
from api.chunk_manifest import build_manifest


def test_cap_pool_cpu() -> None:
    assert Cap(None).pool == "cpu_pool"


def test_cap_pool_small_large() -> None:
    assert Cap(Accel("x", 12, 10)).pool == "small_gpu_pool"
    assert Cap(Accel("x", 24, 20)).pool == "large_gpu_pool"


def test_runtime_payload() -> None:
    payload = Cap(Accel("x", 12, 10), engines=["python"]).runtime("rt1", "node1")
    assert payload["runtime_id"] == "rt1"
    assert payload["pool"] == "small_gpu_pool"
    assert payload["gpu_memory_gb"] == 12


def test_chunk_manifest(tmp_path) -> None:
    file_path = tmp_path / "artifact.bin"
    file_path.write_bytes(b"abcdef")
    manifest = build_manifest(file_path, chunk_size=2, sources=["node://a"])
    assert manifest["artifact_hash"].startswith("sha256:")
    assert len(manifest["chunks"]) == 3
    assert manifest["chunks"][0]["sources"] == ["node://a"]
