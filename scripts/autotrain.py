from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.autotrain import run_autotrain


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Ailovanta AutoTrain loop")
    parser.add_argument("--core-path", default=None)
    parser.add_argument("--work-dir", default="runtime_data/autotrain_pipeline")
    parser.add_argument("--min-events", type=int, default=1)
    parser.add_argument("--event-limit", type=int, default=1000)
    parser.add_argument("--no-reuse-pack", action="store_true")
    parser.add_argument("--model-id", default="ailovanta-owned")
    parser.add_argument("--target-version", default="candidate")
    parser.add_argument("--base-model", default=None)
    parser.add_argument("--model-backend", default=None)
    parser.add_argument("--backend-device", default=None)
    parser.add_argument("--backend-max-steps", type=int, default=None)
    parser.add_argument("--backend-lr", type=float, default=None)
    parser.add_argument("--training-command", default=None)
    parser.add_argument("--execute-checkpoints", action="store_true")
    parser.add_argument("--allow-shadow-import", action="store_true")
    parser.add_argument("--no-prepare-runtime", action="store_true")
    args = parser.parse_args()

    result = run_autotrain(
        core_path=args.core_path,
        work_dir=args.work_dir,
        min_events=args.min_events,
        event_limit=args.event_limit,
        reuse_latest_pack=not args.no_reuse_pack,
        model_id=args.model_id,
        target_version=args.target_version,
        base_model=args.base_model,
        model_backend=args.model_backend,
        backend_device=args.backend_device,
        backend_max_steps=args.backend_max_steps,
        backend_lr=args.backend_lr,
        training_command=args.training_command,
        execute_checkpoints=args.execute_checkpoints,
        allow_shadow_import=args.allow_shadow_import,
        prepare_runtime=not args.no_prepare_runtime,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
