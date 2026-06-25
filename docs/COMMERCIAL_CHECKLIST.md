# Commercial Checklist

This checklist is the gap between the local owned-runtime scaffold and a commercial deployment.

## Code gate

```text
python validate.py
python -m pytest -q
python scripts/aio.py --core-path ../ailovanta-core
python scripts/prod_ready.py --result runtime_data/local_loop/foundation_result.json
```

## Required external resources

```text
HTTPS domain
production database or durable SQLite volume strategy
object storage / model registry
real GPU worker pool
real model checkpoint files
worker credentials / attestation
external anchor / chain adapter
monitoring and alerting
backup and recovery
rate limits and abuse controls
security review
incident rollback process
```

## Must pass before public commercial use

```text
release gate returns release_pass
prod_ready returns production_ready
route_health returns ok
owned-chat-default returns owned_model_ready true
rollback disables/restores active route
worker result requires valid node proof
artifact hash and anchor record exist
```

## Current local scaffold

```text
LocalArtifactStore
FileAnchorAdapter
RouteBook
RouteHealth
ReleaseGate
Worker IO API
AIO local loop
```

## Do not claim until true

```text
Do not claim production foundation model until real trained weights exist.
Do not claim real decentralization until external anchor and independent workers exist.
Do not claim commercial reliability until monitoring, backups, security review, and abuse controls exist.
```
