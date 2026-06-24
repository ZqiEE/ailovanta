# Foundation Import

## Purpose

After core runs a foundation job, public must import the produced result and make it usable.

## Flow

```text
result json
-> core result record
-> runtime model record
-> chain event
-> owned chat route
```

## CLI

```bash
python scripts/import_foundation_result.py runtime_data/foundation_result.json
```

## API module

```text
api.foundation_result_api
POST /foundation/results/import
```

## Import steps

```text
1. Register core result
2. Register runtime model
3. Append chain event
```
