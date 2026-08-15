from __future__ import annotations

from api.model_lock import ModelLockStore


def test_first_digest_is_locked_and_same_digest_verifies(tmp_path):
    store = ModelLockStore(tmp_path / "locks.json")
    first = store.ensure("coder:test", "sha256:first")
    assert first["status"] == "verified"
    assert first["recorded_now"] is True

    same = store.ensure("coder:test", "sha256:first")
    assert same["status"] == "verified"
    assert same["match"] is True


def test_silent_digest_change_is_not_accepted(tmp_path):
    store = ModelLockStore(tmp_path / "locks.json")
    store.ensure("coder:test", "sha256:first")
    changed = store.ensure("coder:test", "sha256:second")
    assert changed["status"] == "mismatch"
    assert changed["expected_digest"] == "sha256:first"
    assert changed["actual_digest"] == "sha256:second"


def test_explicit_model_change_replaces_lock(tmp_path):
    store = ModelLockStore(tmp_path / "locks.json")
    store.ensure("coder:test", "sha256:first")
    accepted = store.ensure("coder:test", "sha256:second", accept_change=True)
    assert accepted["status"] == "verified"
    assert accepted["accepted_change"] is True
    assert store.check("coder:test", "sha256:second")["match"] is True
