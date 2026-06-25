from api.node_proof import attach_proof, verify_proof


def test_node_proof_valid() -> None:
    payload = {"id": "x", "task_id": "t1", "node_id": "n1"}
    signed = attach_proof(payload, "n1", "secret")
    assert verify_proof(signed, {"n1": "secret"})["ok"] is True


def test_node_proof_bad_secret() -> None:
    payload = {"id": "x", "task_id": "t1", "node_id": "n1"}
    signed = attach_proof(payload, "n1", "secret")
    assert verify_proof(signed, {"n1": "wrong"})["ok"] is False
