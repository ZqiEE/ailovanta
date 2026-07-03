from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.autotruth_store import AutoTruthEventStore


SAMPLES = [
    {
        "input": "Write a Python function add(a, b) that returns the sum.",
        "output": "def add(a, b):\n    return a + b\n",
        "source": "ailovanta-owned-code-bootstrap",
    },
    {
        "input": "Write a Python function is_even(n) that returns True for even integers.",
        "output": "def is_even(n):\n    return n % 2 == 0\n",
        "source": "ailovanta-owned-code-bootstrap",
    },
    {
        "input": "Write a Python function reverse_string(s).",
        "output": "def reverse_string(s):\n    return s[::-1]\n",
        "source": "ailovanta-owned-code-bootstrap",
    },
]


def seed_events() -> None:
    store = AutoTruthEventStore()
    for sample in SAMPLES:
        store.add_event(sample)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train Ailovanta-owned-code from scratch initialization")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--score-fallback", type=float, default=0.5)
    args = parser.parse_args()

    seed_events()
    cmd = [
        sys.executable,
        "scripts/autotrain.py",
        "--core-path",
        args.core_path,
        "--model-id",
        "ailovanta-owned-code",
        "--target-version",
        "candidate",
        "--model-backend",
        "transformers-causal-lm",
        "--base-model",
        "scratch:ailovanta-code-tiny",
        "--backend-device",
        args.device,
        "--backend-max-steps",
        str(args.steps),
        "--execute-checkpoints",
        "--allow-shadow-import",
        "--no-reuse-pack",
    ]
    print(json.dumps({"stage": "training_owned_code_model", "cmd": cmd}, ensure_ascii=False, indent=2))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
