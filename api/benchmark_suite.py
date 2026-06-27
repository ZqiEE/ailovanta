from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CASES = [
    {"id": "reverse_string", "prompt": "Write a Python function that reverses a string.", "must_include": ["def", "[::-1]"], "weight": 1.0},
    {"id": "sum_list", "prompt": "Write a Python function that sums a list of numbers.", "must_include": ["def", "sum"], "weight": 1.0},
    {"id": "explain_error", "prompt": "Explain what NameError means in Python.", "must_include": ["NameError", "defined"], "weight": 1.0},
]


def load_cases(path: str | None = None) -> list[dict[str, Any]]:
    if path and Path(path).exists():
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("cases", DEFAULT_CASES)
    return DEFAULT_CASES


def score_text(text: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0.0
    got = 0.0
    details = []
    for case in cases:
        weight = float(case.get("weight", 1.0))
        total += weight
        required = case.get("must_include", [])
        passed = all(str(token).lower() in text.lower() for token in required)
        got += weight if passed else 0.0
        details.append({"id": case.get("id"), "passed": passed, "must_include": required})
    score = round(got / total, 4) if total else 0.0
    return {"score": score, "passed": score >= 0.5, "details": details}


def score_catalog_item(item: dict[str, Any]) -> dict[str, Any]:
    loc = Path(str(item.get("location", "")))
    text = ""
    for name in ["output.json", "artifact.json", "merged.json"]:
        path = loc / name
        if path.exists():
            text += path.read_text(encoding="utf-8", errors="ignore")
    metrics = item.get("metrics") or {}
    base_score = float(metrics.get("score", 0.0))
    exists_score = 0.4 if loc.exists() else 0.0
    metric_score = min(base_score, 1.0) * 0.6
    final = round(exists_score + metric_score, 4)
    return {"score": final, "passed": final >= 0.5, "location_exists": loc.exists(), "metadata_chars": len(text), "metrics": metrics}
