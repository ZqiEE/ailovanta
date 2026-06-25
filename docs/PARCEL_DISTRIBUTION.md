# Parcel Distribution

## Purpose

Parcel distribution is the public side handoff layer between core bundle generation and remote node execution.

## App entrypoint

```bash
uvicorn api.main_packet:app --reload
```

## API

```text
POST /parcels/push
GET /parcels/pending
POST /parcels/submit
GET /parcels/submitted
```

## Push a core bundle

```bash
python scripts/push_bundle_packet.py runtime_data/task_bundle/task_bundle.json
```

## List pending items

```bash
python scripts/list_parcels.py
```

## Submit a node result

```bash
python scripts/submit_parcel.py runtime_data/node_task/receipt.json
```

## Flow

```text
core task bundle
-> public parcels push
-> pending list
-> node result submit
-> submitted list
```

## Next step

Convert submitted parcels back into core-compatible receipts and finalize the artifact.
