from api.compat_check import check_real_training_requirements, classify_base_model_ref, select_real_training_backend, training_backend_from_payload


def test_real_training_preflight_reports_gpu_and_missing_base_path() -> None:
    result = check_real_training_requirements(
        {
            "real": True,
            "use_transformers": True,
            "peft": True,
            "lora": True,
            "requires_gpu": True,
            "base_model": "Z:/missing/ailovanta-model",
        },
        {"has_gpu": False},
    )

    assert result["ok"] is False
    assert result["backend"] == "lora"
    assert "gpu_required_but_node_has_no_gpu" in result["blockers"]
    assert "base_model_path_missing" in result["blockers"]


def test_real_training_preflight_classifies_qlora() -> None:
    assert training_backend_from_payload({"qlora": True, "peft": True}) == "qlora"
    assert classify_base_model_ref("sshleifer/tiny-gpt2")["kind"] == "hf_or_remote"


def test_real_training_backend_auto_prefers_lora_when_gpu_is_available() -> None:
    plan = select_real_training_backend(
        {"real": True, "use_transformers": True, "training_backend": "auto"},
        profile={"has_gpu": True, "available_gpu_memory_gb": 16},
        stack={
            "system": "Windows",
            "modules": [
                {"name": "torch", "installed": True},
                {"name": "transformers", "installed": True},
                {"name": "datasets", "installed": True},
                {"name": "peft", "installed": True},
                {"name": "bitsandbytes", "installed": False},
            ],
            "cuda": {"available": True},
        },
    )

    assert plan["requested_backend"] == "auto"
    assert plan["selected_backend"] == "lora"
    assert plan["reason"] == "auto_selection:lora_gpu_available"
