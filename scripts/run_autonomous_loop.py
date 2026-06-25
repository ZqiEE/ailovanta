from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one full Ailovanta autonomous learning cycle")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--baseline-score", type=float, default=0.45)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--allow-shadow-import", action="store_true")
    parser.add_argument("--execute-checkpoints", action="store_true")
    parser.add_argument("--checkpoint-output-root", default=None)
    parser.add_argument("--training-command", default=None)
    args = parser.parse_args()
    payload = {
        "core_path": args.core_path,
        "baseline_score": args.baseline_score,
        "max_steps": args.max_steps,
        "allow_shadow_import": args.allow_shadow_import,
        "execute_checkpoints": args.execute_checkpoints,
        "checkpoint_output_root": args.checkpoint_output_root,
        "training_command": args.training_command,
    }
    with httpx.Client(timeout=900) as client:
        response = client.post(args.api_url.rstrip("/") + "/autonomous/run", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
