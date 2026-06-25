from __future__ import annotations

import argparse
import json

from api.autonomous_loop import AutonomousLoop


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local autonomous loop with model preparation")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--root", default="runtime_data/autonomous_loop")
    parser.add_argument("--baseline-score", type=float, default=0.45)
    parser.add_argument("--execute-checkpoints", action="store_true")
    parser.add_argument("--model-backend", default=None)
    parser.add_argument("--base-model", default=None)
    parser.add_argument("--backend-device", default=None)
    parser.add_argument("--backend-max-steps", type=int, default=None)
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    args = parser.parse_args()
    result = AutonomousLoop(core_path=args.core_path, root=args.root).run_once(
        baseline_score=args.baseline_score,
        execute_checkpoints=args.execute_checkpoints,
        model_backend=args.model_backend,
        base_model=args.base_model,
        backend_device=args.backend_device,
        backend_max_steps=args.backend_max_steps,
        runtime_id=args.runtime_id,
        node_id=args.node_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
