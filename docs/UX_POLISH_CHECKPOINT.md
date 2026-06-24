# Guest Chat Polish Checkpoint

Status: guest chat polish pass in progress

## Completed in this pass

```text
Clear guest data control added to the Guest Session panel.
Copy chat control added to the chat panel.
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
Copy chat
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
3. Confirm Copy chat appears in the chat controls.
4. Confirm empty conversation list says: No conversations yet. Start a new guest chat.
5. Stop the API and reload to confirm the offline message gives the uvicorn command.
6. Start the API again and confirm chat still works.
7. Send a message, then use Copy chat to copy the conversation text.
```

## Next safe polish

```text
Model runtime connected indicator
Better mobile spacing
Conversation title edit
Export chat as text file
Copy individual message
```
