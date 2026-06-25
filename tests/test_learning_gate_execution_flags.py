from pathlib import Path

from api.learning_gate import build_foundation_command, build_eval_payload


def test_build_foundation_command_with_execution_flags(tmp_path: Path) -> None:
    command = build_foundation_command(
        tmp_path,
        tmp_path / "job.json",
        tmp_path / "result.json",
        execute_checkpoints=True,
        checkpoint_output_root=tmp_path / "ckpts",
        training_command="python scripts/default_train_checkpoint.py",
    )
    assert "--execute-checkpoints" in command
    assert "--checkpoint-output-root" in command
    assert "--training-command" in command


def test_eval_payload_rewards_local_execution() -> None:
    payload = build_eval_payload({"artifact": {"metrics": {"avg_eval_loss": 0.5, "accepted_checkpoints": 1, "execution_mode": "local"}, "artifact_hash": "sha256:x"}})
    names = [item["name"] for item in payload["metrics"]]
    assert "checkpoint_execution" in names
