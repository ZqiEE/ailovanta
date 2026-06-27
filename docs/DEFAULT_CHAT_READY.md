# Default Chat Readiness

Commercial checklist item:

```text
owned-chat-default returns owned_model_ready true
```

Probe API:

```text
GET /ops/default-chat/ready?route_key=owned-chat/default
```

The probe calls the same internal default route path used by owned-chat default and checks:

```text
ok == true
owned_model_ready == true
```

This check is included in `prod_ready_plus` as a blocker:

```text
owned_chat_default:not_ready
```

Release gate calls `prod_ready_plus`, so a failed default chat readiness probe blocks `release_pass`.
