# Reputation

v1.4 adds a first node reputation layer.

## API

```text
GET /reputation/leaderboard
GET /reputation/summary
```

## Score inputs

- node trust
- compute score
- GPU availability
- current node status

## Export

```bash
python scripts/export_reputation.py --api-url http://127.0.0.1:8000
```

Default output:

```text
runtime_data/reputation_leaderboard.json
```

## Why it matters

A GPU network needs ranking before it can route important jobs. The MVP score is simple, but it creates a place to improve trust, uptime, verification, and contribution history later.
