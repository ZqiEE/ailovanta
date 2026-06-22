# API Reference

Base URL for local runtime:

```text
http://127.0.0.1:8000
```

## Health

```text
GET /
GET /network/status
```

## Nodes

```text
POST /nodes/register
POST /nodes/heartbeat
```

## Jobs

```text
GET  /jobs
GET  /jobs/next
POST /jobs/result
POST /jobs/retry-failed
POST /jobs/requeue-stale
```

## Private AI

```text
POST /ai/chat
GET  /memory
POST /memory
DELETE /memory
```

## Verification

```text
GET /verification/status
```

## Training

```text
POST /training/jobs
GET  /training/jobs
POST /models/versions
GET  /models/versions
```

## Minimal flow

1. Register node
2. Fetch next job
3. Submit result
4. Check verification status
5. Create training job
6. Register model version
