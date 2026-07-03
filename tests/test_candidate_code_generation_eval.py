import json

from api.candidate_code_generation_eval import evaluate_candidate_code_generation
from api.transformers_artifact import peft_adapter_base_model_ref


def test_candidate_code_generation_eval_blocks_lightweight_backend() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "lightweight-ngram"})

    assert result["ok"] is False
    assert "unsupported_code_generation_backend" in result["blockers"]


def test_candidate_code_generation_eval_requires_ready_transformers_backend() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"})

    assert result["ok"] is False
    assert "backend_ref_unsupported" in result["blockers"]


def test_candidate_code_generation_eval_reports_model_load_failure(tmp_path) -> None:
    model_dir = tmp_path / "bad-model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local", "backend_ref": model_dir.resolve().as_uri()})

    assert result["ok"] is False
    assert set(result["blockers"]) & {"transformers_model_load_failed", "transformers_runtime_unavailable"}


def test_candidate_code_generation_eval_runs_generated_code() -> None:
    def generator(case, _binding):
        if case["case_id"] == "python_add":
            return "def add(left, right):\n    return left + right\n"
        return "def reverse_string(value):\n    return value[::-1]\n"

    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"}, generator=generator)

    assert result["ok"] is True
    assert result["blockers"] == []
    assert result["passed_cases"] == result["total_cases"] == 2
    assert result["score"] == 1.0
    assert all(case["passed"] for case in result["cases"])


def test_candidate_code_generation_eval_fails_bad_generated_code() -> None:
    def generator(_case, _binding):
        return "def add(left, right):\n    return 0\n\ndef reverse_string(value):\n    return value\n"

    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"}, generator=generator)

    assert result["ok"] is False
    assert "benchmark_failed" in result["blockers"]
    assert result["score"] < 1.0
    assert any(not case["passed"] for case in result["cases"])


def test_adapter_base_model_ref_prefers_training_output_for_lora(tmp_path) -> None:
    model_dir = tmp_path / "adapter"
    model_dir.mkdir()
    (model_dir / "adapter_config.json").write_text(json.dumps({"base_model_name_or_path": "wrong-base"}), encoding="utf-8")
    (model_dir / "output.json").write_text(
        json.dumps(
            {
                "schema": "ailovanta.model_output.v1",
                "base_model": "right-base",
                "metrics": {"backend": "lora"},
            }
        ),
        encoding="utf-8",
    )

    assert peft_adapter_base_model_ref(model_dir) == "right-base"


def test_adapter_base_model_ref_falls_back_to_adapter_config(tmp_path) -> None:
    model_dir = tmp_path / "adapter"
    model_dir.mkdir()
    (model_dir / "adapter_config.json").write_text(json.dumps({"base_model_name_or_path": "adapter-base"}), encoding="utf-8")

    assert peft_adapter_base_model_ref(model_dir) == "adapter-base"
