from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from api.secret_filter import scan_text

CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp", ".cs", ".php", ".rb", ".swift", ".kt", ".kts", ".sql", ".sh", ".ps1", ".html", ".css", ".json", ".yaml", ".yml", ".toml",
}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", ".next", "__pycache__", ".pytest_cache", "runtime_data", "coverage", ".mypy_cache", ".ruff_cache"}
LICENSE_FILES = {"license", "license.md", "license.txt", "copying", "copying.txt"}
LOW_VALUE_FILE_HINTS = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", ".min.js", ".min.css", ".bundle.js", "coverage-final.json", "tsconfig.tsbuildinfo"}
SYNTAX_HINTS = {"syntax", "grammar", "basic", "basics", "tutorial", "example", "examples", "intro", "getting_started", "playground", "sample"}
ALGORITHM_HINTS = {
    "algorithm", "algorithms", "data_structure", "data_structures", "array", "string", "hash", "heap", "stack", "queue", "linked",
    "list", "tree", "graph", "trie", "union_find", "disjoint_set", "segment_tree", "fenwick", "sort", "search", "binary_search",
    "bfs", "dfs", "dijkstra", "astar", "dp", "dynamic_programming", "backtracking", "greedy", "sliding_window", "two_pointer",
}
API_HINTS = {"api", "client", "sdk", "http", "request", "response", "handler", "router", "service"}
TEST_HINTS = {"test", "tests", "__tests__", "spec", "e2e", "integration"}
_LAST_STATS: dict[str, int] = {
    "scanned": 0,
    "accepted": 0,
    "skipped_secret": 0,
    "skipped_short": 0,
    "skipped_read_error": 0,
    "skipped_low_value": 0,
    "tagged_syntax_foundation": 0,
    "tagged_algorithmic_core": 0,
    "tagged_api_usage": 0,
    "tagged_test_driven_sample": 0,
}


@dataclass(frozen=True)
class CodeRecord:
    source_root: str
    path: str
    language: str
    bytes: int
    sha256: str
    license_hint: str
    secret_scan_status: str
    curriculum_tags: list[str]
    priority_tier: str
    priority_score: int
    text: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


def last_stats() -> dict[str, int]:
    return dict(_LAST_STATS)


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript-react", ".js": "javascript", ".jsx": "javascript-react", ".java": "java", ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c", ".h": "c-header", ".hpp": "cpp-header", ".cs": "csharp", ".php": "php", ".rb": "ruby", ".swift": "swift", ".kt": "kotlin", ".kts": "kotlin", ".sql": "sql", ".sh": "shell", ".ps1": "powershell", ".html": "html", ".css": "css", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".md": "markdown",
    }.get(ext, ext.removeprefix(".") or "text")


def file_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def license_hint(root: Path) -> str:
    for child in root.iterdir() if root.exists() and root.is_dir() else []:
        if child.name.lower() in LICENSE_FILES and child.is_file():
            try:
                text = child.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
            except Exception:
                return "license_file_present"
            for name in ["mit", "apache", "bsd", "mpl", "isc", "unlicense", "gpl", "lgpl", "agpl"]:
                if name in text:
                    return name
            return "license_file_present"
    return "unknown"


def iter_code_files(root: Path, max_file_bytes: int = 512_000) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def classify_curriculum(path: Path, root: Path, text: str) -> tuple[list[str], int]:
    tags: list[str] = []
    score = 0
    rel = str(path.resolve().relative_to(root)).lower().replace("\\", "/")
    name = path.name.lower()
    ext = path.suffix.lower()

    if any(hint in rel for hint in ALGORITHM_HINTS):
        tags.append("algorithmic_core")
        score += 140
    if any(hint in rel for hint in TEST_HINTS):
        tags.append("test_driven_sample")
        score += 120
    if any(hint in rel for hint in SYNTAX_HINTS):
        tags.append("syntax_foundation")
        score += 110
    if any(hint in rel for hint in API_HINTS):
        tags.append("api_usage")
        score += 90

    if ext in {".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".cs", ".swift", ".kt"}:
        score += 25
    if len(text) <= 6000:
        score += 10
    if re.search(r"\b(import|from|using|require|include)\b", text):
        score += 10
    if re.search(r"\b(class|def|function|func|interface|struct|impl)\b", text):
        score += 10

    if "syntax_foundation" not in tags and ext in {".py", ".js", ".ts"} and len(text.splitlines()) <= 80:
        tags.append("syntax_foundation")
        score += 40
    if "api_usage" not in tags and re.search(r"\b(request|response|client|router|handler|service)\b", text.lower()):
        tags.append("api_usage")
        score += 35

    if not tags:
        tags.append("project_usage")
        score += 20
    return sorted(set(tags)), score


def priority_tier(score: int) -> str:
    if score >= 180:
        return "high"
    if score >= 90:
        return "medium"
    return "baseline"


def low_value_reason(path: Path, text: str) -> str | None:
    rel = str(path).lower().replace("\\", "/")
    name = path.name.lower()
    if name in LOW_VALUE_FILE_HINTS or any(hint in rel for hint in LOW_VALUE_FILE_HINTS):
        return "generated_or_lockfile"
    if len(text) > 20000 and text.count("\n") < 20:
        return "minified_or_dense_blob"
    if path.suffix.lower() in {".json", ".yaml", ".yml", ".toml"} and not re.search(r"\b(function|class|api|route|handler|query|schema)\b", text.lower()):
        return "config_noise"
    return None


def build_records(root: str | Path, max_file_bytes: int = 512_000) -> list[CodeRecord]:
    base = Path(root).resolve()
    hint = license_hint(base)
    stats = {
        "scanned": 0,
        "accepted": 0,
        "skipped_secret": 0,
        "skipped_short": 0,
        "skipped_read_error": 0,
        "skipped_low_value": 0,
        "tagged_syntax_foundation": 0,
        "tagged_algorithmic_core": 0,
        "tagged_api_usage": 0,
        "tagged_test_driven_sample": 0,
    }
    records: list[CodeRecord] = []
    for path in iter_code_files(base, max_file_bytes=max_file_bytes):
        stats["scanned"] += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            stats["skipped_read_error"] += 1
            continue
        clean = text.strip()
        if len(clean) < 40:
            stats["skipped_short"] += 1
            continue
        scan = scan_text(clean)
        if not scan.ok:
            stats["skipped_secret"] += 1
            continue
        if low_value_reason(path, clean):
            stats["skipped_low_value"] += 1
            continue
        rel = str(path.resolve().relative_to(base))
        tags, score = classify_curriculum(path, base, clean)
        for tag in tags:
            stats_key = "tagged_" + tag
            if stats_key in stats:
                stats[stats_key] += 1
        records.append(
            CodeRecord(
                source_root=str(base),
                path=rel,
                language=detect_language(path),
                bytes=len(clean.encode("utf-8", errors="ignore")),
                sha256=file_hash(clean),
                license_hint=hint,
                secret_scan_status="ok",
                curriculum_tags=tags,
                priority_tier=priority_tier(score),
                priority_score=score,
                text=clean,
            )
        )
        stats["accepted"] += 1
    records.sort(key=lambda item: (item.priority_score, -item.bytes, item.path), reverse=True)
    _LAST_STATS.clear()
    _LAST_STATS.update(stats)
    return records


def write_jsonl(records: list[CodeRecord], output: str | Path) -> dict:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(record.to_json() + "\n")
    return {
        "schema_version": "ailovanta.code_corpus.v1",
        "output": str(target),
        "records": len(records),
        "bytes": sum(record.bytes for record in records),
        "languages": sorted({record.language for record in records}),
        "stats": last_stats(),
    }
