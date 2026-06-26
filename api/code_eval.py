from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def eval_python_syntax(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    total = 0
    passed = 0
    errors: list[dict[str, str]] = []
    for path in base.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__", "runtime_data"} for part in path.parts):
            continue
        total += 1
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
            passed += 1
        except Exception as exc:
            errors.append({"path": str(path), "error": str(exc)})
    return {"name": "python_syntax", "total": total, "passed": passed, "failed": total - passed, "errors": errors[:20]}


def eval_json_files(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    total = 0
    passed = 0
    errors: list[dict[str, str]] = []
    for path in base.rglob("*.json"):
        if any(part in {".git", ".venv", "venv", "node_modules", "runtime_data"} for part in path.parts):
            continue
        total += 1
        try:
            json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            passed += 1
        except Exception as exc:
            errors.append({"path": str(path), "error": str(exc)})
    return {"name": "json_parse", "total": total, "passed": passed, "failed": total - passed, "errors": errors[:20]}


def run_optional(cmd: list[str], cwd: str | Path, name: str, timeout: int = 120) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"name": name, "available": False, "passed": 0, "failed": 0, "returncode": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "available": True, "passed": 0, "failed": 1, "returncode": None, "stdout": exc.stdout or "", "stderr": "timeout"}
    ok = proc.returncode == 0
    return {"name": name, "available": True, "passed": 1 if ok else 0, "failed": 0 if ok else 1, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def eval_repo(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    checks = [eval_python_syntax(base), eval_json_files(base)]
    if (base / "pytest.ini").exists() or (base / "pyproject.toml").exists() or any(base.glob("tests/test_*.py")):
        checks.append(run_optional([sys.executable, "-m", "pytest", "-q"], base, "pytest"))
    if (base / "package.json").exists():
        checks.append(run_optional(["npm", "run", "typecheck"], base, "npm_typecheck"))
    total = sum(int(c.get("total", c.get("passed", 0) + c.get("failed", 0)) or 0) for c in checks)
    passed = sum(int(c.get("passed", 0) or 0) for c in checks)
    failed = sum(int(c.get("failed", 0) or 0) for c in checks)
    score = round(passed / max(passed + failed, 1), 4)
    return {"schema_version": "ailovanta.code_eval.v1", "root": str(base.resolve()), "score": score, "passed": passed, "failed": failed, "total": total, "checks": checks}


def save_eval(result: dict[str, Any], path: str | Path = "runtime_data/code_eval.json") -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
