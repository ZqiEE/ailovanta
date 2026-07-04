from pathlib import Path

from api.code_repair import verified_repair


def test_verified_repair_records_successful_fix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_AUTOTRUTH_PATH", str(tmp_path / "events.sqlite3"))
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text("from calc import add\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")
    result = verified_repair(
        tmp_path,
        "pytest",
        replacements=[{"path": "calc.py", "old": "return a - b", "new": "return a + b"}],
    )
    assert result["ok"] is True
    assert result["stage"] == "repair_verified"
    assert result["training_event"] is not None
