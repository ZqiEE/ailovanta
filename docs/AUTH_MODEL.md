# Ailovanta Access Model

Current MVP access method:

```text
Guest mode first
```

Ailovanta should not require login, payment, wallet connection, or GitHub OAuth for the first user experience.

The first version should let people open the product and use the chat immediately.

## Current first-use flow

```text
1. User opens Ailovanta.
2. User can send a message immediately.
3. Ailovanta creates a local guest id in the browser or API client.
4. Conversations are stored under the guest id.
5. User sees value before being asked to create an account.
```

## Why login is deferred

```text
Login before value adds friction.
Payment before value kills conversion.
Wallet before value confuses normal users.
GitHub-only login limits the audience too early.
```

## Current product rule

```text
No required login.
No required payment.
No required wallet.
No required GitHub account.
```

## Optional technical endpoints

The repository may still contain GitHub OAuth backend endpoints for later developer mode:

```text
GET  /auth/github/login
GET  /auth/github/callback
GET  /auth/me
POST /auth/logout
```

These are not the default user path.

## Identity model for MVP

```text
Guest User
  -> guest_id
  -> conversations
  -> local usage records

Future Account
  -> optional GitHub login
  -> optional workspace
  -> optional API keys
  -> optional billing
```

## When to add login later

Add login only after users need one of these:

```text
sync across devices
save long-term history
create API keys
join a workspace
run a node
access private models
manage billing
```

## What not to do now

Do not force GitHub login for the first chat.

Do not force email login for the first chat.

Do not force wallet login for the first chat.

Do not show a payment wall before the user gets value.

Do not make auth the center of the product before the product itself feels useful.

## Final rule

```text
First prove value.
Then ask for identity.
Then ask for payment.
```
