from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"
api = root / "api" / "main.py"
ollama = root / "api" / "ollama_adapter.py"
memory = root / "api" / "memory_store.py"
node_client = root / "node_client" / "client.py"
runtime_doc = root / "docs" / "LOCAL_RUNTIME.md"
ollama_doc = root / "docs" / "OLLAMA.md"
requirements = root / "requirements.txt"
env_example = root / ".env.example"

for path in [index, readme, api, ollama, memory, node_client, runtime_doc, ollama_doc, requirements, env_example]:
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = index.read_text(encoding="utf-8")
required_html = [
    "Open GPU Privacy AI",
    "Run a node. Use private AI for free.",
    "Node Client",
    "API Skeleton",
    "Protocol",
    "Pricing",
    "Waitlist",
    "Training Simulator",
    "Robot Memory",
]
for marker in required_html:
    assert marker in html, f"missing html marker: {marker}"

api_text = api.read_text(encoding="utf-8")
for marker in [
    "FastAPI",
    "OllamaAdapter",
    "MemoryStore",
    "/nodes/register",
    "/jobs/next",
    "/ai/chat",
    "/memory",
    "/network/status",
]:
    assert marker in api_text, f"missing api marker: {marker}"

ollama_text = ollama.read_text(encoding="utf-8")
for marker in ["OllamaAdapter", "OLLAMA_MODEL", "/api/chat"]:
    assert marker in ollama_text, f"missing ollama marker: {marker}"

memory_text = memory.read_text(encoding="utf-8")
for marker in ["MemoryStore", "list", "add", "wipe"]:
    assert marker in memory_text, f"missing memory marker: {marker}"

client_text = node_client.read_text(encoding="utf-8")
for marker in ["register_node", "heartbeat", "worker_loop", "psutil"]:
    assert marker in client_text, f"missing node client marker: {marker}"

assert "fastapi" in requirements.read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in env_example.read_text(encoding="utf-8")
assert html.count("<section") >= 8, "expected v0.3+ product sections"

print("Validation passed.")
