from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"

assert index.exists(), "index.html is missing"
assert readme.exists(), "README.md is missing"

html = index.read_text(encoding="utf-8")
required = [
    "Open GPU Privacy AI",
    "贡献 GPU 免费用",
    "不开节点，付费使用",
    "阅后即焚",
    "训练引擎",
    "机器人记忆",
    "RAG",
    "LoRA",
]
for marker in required:
    assert marker in html, f"missing marker: {marker}"

assert "<script>" in html and "</script>" in html, "script block missing"
assert html.count("<section") >= 5, "expected multiple product sections"

print("Validation passed.")
