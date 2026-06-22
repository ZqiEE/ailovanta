# Node Identity

v1.3 adds a stable local node id.

## Files

```text
runtime_data/node_identity.json
```

## API

```text
POST /nodes/register
GET  /nodes
GET  /dashboard/nodes
```

## Helper

```bash
python scripts/show_node_identity.py
```

## Client

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --identity-path runtime_data/node_identity.json
```

## Reason

A stable node id lets the scheduler keep trust, uptime, contribution, and status history across restarts.
