from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"
api = root / "api" / "main.py"
ollama = root / "api" / "ollama_adapter.py"
memory = root / "api" / "memory_store.py"
node_client = root / "node_client" / "client.py"
node_device = root / "node_client" / "device.py"
resource_guard = root / "node_client" / "resource_guard.py"
job_runner = root / "node_client" / "job_runner.py"
runtime_doc = root / "docs" / "LOCAL_RUNTIME.md"
ollama_doc = root / "docs" / "OLLAMA.md"
node_doc = root / "docs" / "NODE_CLIENT.md"
requirements = root / "requirements.txt"
env_example = root / ".env.example"

for path in [
    index,
    readme,
    api,
    ollama,
    memory,
    node_client,
    node_device,
    resource_guard,
    job_runner,
    runtime_doc,
    ollama_doc,
    node_doc,
    requirements,
    env_example,
]:
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = index.read_text(encoding="utf-8")
for marker in [
    "Open GPU Privacy AI",
    "Run a node. Use private AI for free.",
    "Node Client",
    "API Skeleton",
    "Protocol",
    "Pricing",
    "Waitlist",
    "Training Simulator",
    "Robot Memory",
]:
    assert marker in html, f"missing html marker: {marker}"

api_text = api.read_text(encoding="utf-8")
for marker in ["FastAPI", "OllamaAdapter", "MemoryStore", "/nodes/register", "/jobs/next", "/ai/chat", "/memory"]:
    assert marker in api_text, f"missing api marker: {marker}"

client_text = node_client.read_text(encoding="utf-8")
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop"]:
    assert marker in client_text, f"missing node client marker: {marker}"

device_text = node_device.read_text(encoding="utf-8")
for marker in ["DeviceProfile", "detect_device", "detect_nvidia_gpu", "nvidia-smi"]:
    assert marker in device_text, f"missing device marker: {marker}"

resource_text = resource_guard.read_text(encoding="utf-8")
for marker in ["ResourceGuard", "ResourceLimits", "can_run_job"]:
    assert marker in resource_text, f"missing resource marker: {marker}"

runner_text = job_runner.read_text(encoding="utf-8")
for marker in ["JobRunner", "JobRunResult", "simulated sandboxed result"]:
    assert marker in runner_text, f"missing runner marker: {marker}"

assert "fastapi" in requirements.read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in env_example.read_text(encoding="utf-8")
assert html.count("<section") >= 8, "expected v0.3+ product sections"

print("Validation passed.")
