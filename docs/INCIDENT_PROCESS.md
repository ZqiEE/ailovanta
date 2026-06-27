# Incident Process

Use the incident-ready app entry:

```bash
uvicorn api.main_incident_ready:app --host 0.0.0.0 --port 8000
```

Plan response from current alerts:

```text
POST /ops/incidents/plan
{"route_key":"owned-chat/default","verify_bytes":true,"dry_run":true}
```

Dry-run execution:

```text
POST /ops/incidents/execute
{"route_key":"owned-chat/default","verify_bytes":true,"dry_run":true}
```

Apply execution:

```text
POST /ops/incidents/execute
{"route_key":"owned-chat/default","verify_bytes":true,"dry_run":false}
```

List incident logs:

```text
GET /ops/incidents/logs
```

Behavior:

```text
no high/critical alerts -> observe
high/critical non-route alerts -> create backup only
high/critical route alerts -> create backup, then disable active route
```

Manual rollback APIs are also available from this entry:

```text
POST /rollback/latest
POST /rollback/action
GET /rollback/logs
```
