# Guest Chat Polish Checkpoint

Status: guest chat polish pass started

## Completed in this pass

```text
Clear guest data control added to the Guest Session panel.
Conversation empty state now tells the user to start a new guest chat.
Conversation API failure state now tells the user how to start the local API.
Reset guest id uses the same local guest reset flow.
First-use path still has no login and no payment requirement.
```

## Current UI controls

```text
New chat
Refresh
Send
Clear view
Delete chat
Reset guest id
Clear guest data
```

## Current guest rules

```text
No login required
No payment required
Guest mode first
No wallet step
No access lock
```

## Manual check

```text
1. Open /app.
2. Confirm Clear guest data appears in Guest Session.
3. Confirm empty conversation list says: No conversations yet. Start a new guest chat.
4. Stop the API and reload to confirm the offline message gives the uvicorn command.
5. Start the API again and confirm chat still works.
```

## Next safe polish

```text
Export chat as text
Copy conversation to clipboard
Model runtime connected indicator
Better mobile spacing
Conversation title edit
```
