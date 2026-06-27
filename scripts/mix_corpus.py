from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def read_lines(path: Path, limit: int | None = None) -> list[str]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    return lines[:limit] if limit else lines


def main() -> int:
    p = argparse.ArgumentParser(description="Mix corpus files into one training file")
    p.add_argument("--code", default="runtime_data/code_corpus_github.jsonl")
    p.add_argument("--lessons", default="runtime_data/distill_corpus.jsonl")
    p.add_argument("--output", default="runtime_data/mixed_code_train.jsonl")
    p.add_argument("--code-limit", type=int)
    p.add_argument("--lesson-limit", type=int)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    code = read_lines(Path(args.code), args.code_limit)
    lessons = read_lines(Path(args.lessons), args.lesson_limit)
    rows = code + lessons
    random.Random(args.seed).shuffle(rows)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    print(json.dumps({"ok": bool(rows), "output": str(target), "code_rows": len(code), "lesson_rows": len(lessons), "total_rows": len(rows)}, ensure_ascii=False, indent=2))
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
