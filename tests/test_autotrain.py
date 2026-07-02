from pathlib import Path

import pytest

from api.autotrain import AutoTrainError, build_pack_from_events, ensure_autotrain_pack
from api.autotruth_store import AutoTruthEventStore


def test_build_pack_from_events_creates_sft_rows() -> None:
    pack = build_pack_from_events(
        [
            {"event_id": "evt_1", "input": "write a function", "output": "def fn(): return 1", "behavior": {"score": 0.8}},
            {"event_id": "evt_2", "input": "", "output": "ignored"},
        ],
        model_id="ailovanta-owned",
        target_version="candidate",
    )
    assert pack["pack_id"].startswith("autotrain_pack_")
    assert pack["pack_hash"].startswith("sha256:")
    assert pack["metadata"]["usable_rows"] == 1
    assert pack["sft"][0]["sample_id"] == "evt_1"


def test_ensure_autotrain_pack_imports_latest_pack(tmp_path: Path) -> None:
    store = AutoTruthEventStore(tmp_path / "learning")
    store.add_event({"input": "hello", "output": "world"})
    result = ensure_autotrain_pack(store, reuse_latest_pack=False)
    assert result["created"] is True
    assert result["pack"]["pack_id"].startswith("autotrain_pack_")
    assert store.latest_pack()["pack_id"] == result["pack"]["pack_id"]


def test_ensure_autotrain_pack_requires_events(tmp_path: Path) -> None:
    store = AutoTruthEventStore(tmp_path / "learning")
    with pytest.raises(AutoTrainError):
        ensure_autotrain_pack(store, min_events=1, reuse_latest_pack=False)
