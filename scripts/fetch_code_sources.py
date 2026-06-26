from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def safe_name(value: str) -> str:
    parsed = urlparse(value)
    raw = Path(parsed.path).name or value
    raw = raw.removesuffix(".git")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)[:80]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def fetch_source(source: dict, target_root: Path) -> dict:
    if not source.get("enabled", True):
        return {"name": source.get("name"), "enabled": False, "skipped": True}
    url = source["url"]
    branch = source.get("branch") or "main"
    name = source.get("name") or safe_name(url)
    target = target_root / safe_name(str(name))
    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists() and (target / ".git").exists():
        run(["git", "fetch", "--depth", "1", "origin", branch], cwd=target)
        run(["git", "checkout", branch], cwd=target)
        run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=target)
        action = "updated"
    else:
        run(["git", "clone", "--depth", "1", "--branch", branch, url, str(target)])
        action = "cloned"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(target), text=True).strip()
    return {"name": name, "url": url, "branch": branch, "path": str(target), "commit": commit, "action": action, "license_policy": source.get("license_policy", "unknown")}


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch approved GitHub code sources")
    p.add_argument("--sources", default="runtime_data/github_code_sources.json")
    p.add_argument("--target-root", default="runtime_data/source_repos")
    args = p.parse_args()
    source_path = Path(args.sources)
    if not source_path.exists():
        example = Path("runtime_data.example/github_code_sources.json")
        raise SystemExit(f"sources file not found: {source_path}. Copy {example} first.")
    config = json.loads(source_path.read_text(encoding="utf-8"))
    results = [fetch_source(item, Path(args.target_root)) for item in config.get("sources", [])]
    print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
