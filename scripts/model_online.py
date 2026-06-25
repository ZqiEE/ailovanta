from __future__ import annotations

import argparse
import json

from api.model_warm import ModelWarm, WarmSpec


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a runtime node for a model binding")
    parser.add_argument("--model-key", default="ailovanta-owned:candidate")
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    parser.add_argument("--gpu-memory-gb", type=float, default=24.0)
    parser.add_argument("--region", default="global")
    args = parser.parse_args()
    result = ModelWarm().run(WarmSpec(model_key=args.model_key, runtime_id=args.runtime_id, node_id=args.node_id, gpu_memory_gb=args.gpu_memory_gb, region=args.region))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
