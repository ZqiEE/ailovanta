# Local Loop

Run a local proof/trust/runtime demo loop:

```bash
python scripts/local_loop.py --core-path ../ailovanta-core
```

The runner creates:

```text
runtime_data/local_loop/foundation_plan.json
runtime_data/local_loop/checkpoint_set.json
runtime_data/local_loop/foundation_result.json
runtime_data/local_loop/local_loop_report.json
```

Flow:

```text
local plan
-> node trust registration
-> signed node result
-> outbox
-> proof-required receipt export
-> core checkpoint set
-> foundation artifact v2
-> gg gate
-> gated apply
-> final report
```

A successful run ends with:

```json
{
  "ok": true,
  "final": {
    "stage": "runtime_ready"
  }
}
```

This is a local demo loop. Real GPU training, real nodes, and real chain anchoring still require production infrastructure.
