from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch approved GitHub repos and train code-first loop")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--sources", default="runtime_data/github_code_sources.json")
    p.add_argument("--target-root", default="runtime_data/source_repos")
    p.add_argument("--model-id", default="ailovanta-code")
    p.add_argument("--version", default="v0.1-code")
    p.add_argument("--total-tokens", type=int, default=8192)
    p.add_argument("--shard-tokens", type=int, default=512)
    p.add_argument("--node-runs", type=int, default=8)
    args = p.parse_args()

    fetch = subprocess.run([sys.executable, "scripts/fetch_code_sources.py", "--sources", args.sources, "--target-root", args.target_root], check=False)
    if fetch.returncode != 0:
        return fetch.returncode

    corpus_parts: list[Path] = []
    root = Path(args.target_root)
    for repo in sorted(root.iterdir()) if root.exists() else []:
        if not repo.is_dir():
            continue
        output = Path("runtime_data/code_corpus") / (repo.name + ".jsonl")
        proc = subprocess.run([sys.executable, "scripts/code_corpus.py", "--source", str(repo), "--output", str(output)], check=False)
        if proc.returncode == 0 and output.exists():
            corpus_parts.append(output)

    merged = Path("runtime_data/code_corpus_github.jsonl")
    merged.parent.mkdir(parents=True, exist_ok=True)
    with merged.open("w", encoding="utf-8") as out:
        for part in corpus_parts:
            out.write(part.read_text(encoding="utf-8"))
    if not corpus_parts or merged.stat().st_size == 0:
        raise SystemExit("no code corpus data built")

    train = subprocess.run(
        [
            sys.executable,
            "scripts/full_local_loop.py",
            "--api-url",
            args.api_url,
            "--data-file",
            str(merged),
            "--total-tokens",
            str(args.total_tokens),
            "--shard-tokens",
            str(args.shard_tokens),
            "--node-runs",
            str(args.node_runs),
            "--model-id",
            args.model_id,
            "--version",
            args.version,
        ],
        check=False,
    )
    print(json.dumps({"corpus_parts": [str(p) for p in corpus_parts], "merged_corpus": str(merged), "train_returncode": train.returncode}, ensure_ascii=False, indent=2))
    return train.returncode


if __name__ == "__main__":
    raise SystemExit(main())
