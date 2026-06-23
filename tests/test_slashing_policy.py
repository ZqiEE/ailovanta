from __future__ import annotations

from api.slashing_policy import SlashingPolicy


def test_slashing_policy_penalizes_incident() -> None:
    node = {"node_id": "node_a", "reputation": 0.9, "stake": 2}
    result = SlashingPolicy().evaluate(node, {"type": "bad_output", "severity": "medium"})
    assert result["node_id"] == "node_a"
    assert result["penalty"] > 0
    assert result["new_reputation"] < 0.9
