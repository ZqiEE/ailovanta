from __future__ import annotations

from types import SimpleNamespace

import api.runtime_mode as runtime_mode
import node_client.device as device
import node_client.local_runtime as local_runtime
import node_client.model_profile as model_profile


def _memory(gb: float):
    return SimpleNamespace(total=int(gb * (1024**3)))


def test_24gb_gpu_prefers_qwen3_coder_30b(monkeypatch):
    monkeypatch.setattr(model_profile.psutil, "virtual_memory", lambda: _memory(64))
    monkeypatch.setattr(model_profile, "_nvidia_info", lambda: ("RTX 4090", 24.0))
    profile = model_profile.recommend_local_model()
    assert profile.model == "qwen3-coder:30b"
    assert profile.context_length == 32768


def test_16gb_gpu_prefers_14b(monkeypatch):
    monkeypatch.setattr(model_profile.psutil, "virtual_memory", lambda: _memory(32))
    monkeypatch.setattr(model_profile, "_nvidia_info", lambda: ("RTX GPU", 16.0))
    profile = model_profile.recommend_local_model()
    assert profile.model == "qwen2.5-coder:14b"


def test_16gb_ram_falls_back_to_7b(monkeypatch):
    monkeypatch.setattr(model_profile.psutil, "virtual_memory", lambda: _memory(16))
    monkeypatch.setattr(model_profile, "_nvidia_info", lambda: (None, None))
    monkeypatch.setattr(model_profile.platform, "system", lambda: "Linux")
    profile = model_profile.recommend_local_model()
    assert profile.model == "qwen2.5-coder:7b"


def test_requested_model_tag_must_match_exact_installed_tag():
    installed = {"qwen2.5-coder:7b", "other:latest"}
    assert local_runtime._present(installed, "qwen2.5-coder:7b") is True
    assert local_runtime._present(installed, "qwen2.5-coder:14b") is False
    assert local_runtime._present(installed, "qwen2.5-coder") is True


def test_contributor_profile_does_not_upload_hostname_and_reports_models_privately(monkeypatch):
    monkeypatch.setattr(device.platform, "node", lambda: "secret-personal-hostname")
    monkeypatch.setattr(device.platform, "system", lambda: "Linux")
    monkeypatch.setattr(device, "detect_nvidia_gpu", lambda: (None, None))
    monkeypatch.setattr(device, "installed_ollama_models", lambda: ["qwen2.5-coder:7b"])
    monkeypatch.setattr(device.psutil, "cpu_count", lambda logical=True: 8)
    monkeypatch.setattr(device.psutil, "virtual_memory", lambda: _memory(16))
    profile = device.detect_device()
    assert "secret-personal-hostname" not in profile.device_name
    assert profile.device_name == "Ailovanta Linux Node"
    assert profile.ollama_models == ["qwen2.5-coder:7b"]


def test_private_local_runtime_never_claims_remote_project_transfer(monkeypatch):
    monkeypatch.setenv("AILOVANTA_RUNTIME_MODE", "private-local")
    status = runtime_mode.runtime_privacy_status()
    assert status["private_local"] is True
    assert status["project_files_leave_device"] is False
    assert status["prompt_leaves_device"] is False
    assert status["commercial_model_api_required"] is False
