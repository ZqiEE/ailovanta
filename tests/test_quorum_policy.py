from __future__ import annotations

from api.quorum_policy import QuorumPolicy


def test_quorum_accepts_enough_unique_approvals() -> None:
    decision = QuorumPolicy(required=2, total=3).evaluate(["a", "b", "b"])
    assert decision.passed is True
    assert decision.provided == 2


def test_quorum_rejects_not_enough_approvals() -> None:
    decision = QuorumPolicy(required=3, total=5).evaluate(["a", "b"])
    assert decision.passed is False
