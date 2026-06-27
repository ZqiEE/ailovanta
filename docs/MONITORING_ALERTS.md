# Monitoring and Alerts

Use the monitor-ready app entry:

```bash
uvicorn api.main_monitor_ready:app --host 0.0.0.0 --port 8000
```

Alert summary:

```text
GET /ops/alerts/summary?route_key=owned-chat/default&verify_bytes=true
```

Alert metrics for Prometheus or Grafana:

```text
GET /metrics/alerts
```

Alert summary includes:

```text
prod readiness blockers
route health blockers
runtime route readiness
backup status
abuse controls
runtime node/model availability
```

Severity levels:

```text
critical
high
warning
```

Production should not be considered ready while critical or high alerts exist.
