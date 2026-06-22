from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"

assert index.exists(), "index.html is missing"
assert readme.exists(), "README.md is missing"

html = index.read_text(encoding="utf-8")
required = [
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
for marker in required:
    assert marker in html, f"missing marker: {marker}"

assert "<script>" in html and "</script>" in html, "script block missing"
assert html.count("<section") >= 8, "expected v0.3 product sections"

print("Validation passed.")
