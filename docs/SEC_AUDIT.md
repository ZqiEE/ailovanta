# Sec Audit

Commercial use requires a real security review before public launch.

## Secrets

```text
No real secrets committed to GitHub.
Use deployment secret manager.
Redact secret/token/private_key/password values in logs.
Rotate node secrets before production.
```

## API exposure

```text
Expose only HTTPS through reverse proxy.
Do not expose runtime_data volume.
Do not expose SQLite files.
Protect admin and node registry endpoints.
Separate public chat endpoints from operator endpoints.
```

## Worker safety

```text
Require valid node proof for /wio/result.
Reject inactive nodes.
Store only secret hashes where possible.
Do not accept unsigned checkpoint results.
Verify checkpoint_hash before promotion.
```

## Artifact safety

```text
Every artifact must have sha256 digest.
Every artifact must be tied to checkpoint_set hash.
Every production artifact must be stored in durable storage.
Every promoted artifact should have external anchor record.
```

## Runtime safety

```text
owned-chat-default must go through RouteBook.
RouteHealth must pass before traffic is routed.
Rollback must disable or restore active route.
Runtime doctor blockers must prevent route readiness.
```

## Abuse controls required before public launch

```text
rate limits per user/IP/API key
request body size limits
worker submission size limits
node result replay protection
logging and alerting for failures
manual kill switch for active route
```

## Launch rule

Do not launch publicly until:

```text
prod_ready passes
release gate passes
backup restore drill passes
external artifact storage is configured
external anchor is configured or explicitly waived
security review is signed off
```
