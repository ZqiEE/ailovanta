# Active Route

Ailovanta stores the current owned-chat default model in `RouteBook`.

Default route key:

```text
owned-chat/default
```

## Read current route

```bash
python scripts/route_book.py get --route-key owned-chat/default
```

## Set route manually

```bash
python scripts/route_book.py set \
  --route-key owned-chat/default \
  --model-key ailovanta-owned:candidate
```

## Disable route

```bash
python scripts/route_book.py disable \
  --route-key owned-chat/default \
  --reason rollback
```

## Chat through active route

```text
POST /ailovanta/v1/owned-chat-default
```

Payload:

```json
{
  "prompt": "hello",
  "user_id": "local"
}
```

This endpoint does not require model_id/version. It loads them from the active route.

If no active route exists, it returns `owned-route-unavailable`.

## Route publication

`ra2.apply2()` publishes the active route only when:

```text
proof/trust gate passes
runtime doctor passes
model warm succeeds
```

## Rollback behavior

`RollbackExecutor` now checks active routes during rollback.

If an active route points to the bad model, rollback will disable that route:

```text
owned-chat/default -> bad:model
rollback bad:model
=> owned-chat/default disabled
```

If the live record contains a `previous_model`, rollback restores the same route to the previous model:

```text
owned-chat/default -> bad:model
previous_model = stable:model
rollback bad:model
=> owned-chat/default -> stable:model
```

This prevents `/ailovanta/v1/owned-chat-default` from continuing to route traffic to a rolled-back model.
