# Ailovanta Auth Model

Current MVP login method:

```text
GitHub OAuth only
```

Ailovanta should use GitHub login first because the first real users are expected to be developers, node operators, and technical testers.

Do not add email login, phone login, wallet login, or paid billing login yet.

## Current account model

```text
GitHub account
  -> Ailovanta user
      -> local session
      -> conversations
      -> API usage
      -> future workspace/project records
```

## Implemented local endpoints

```text
GET  /auth/github/login
GET  /auth/github/callback
GET  /auth/me
POST /auth/logout
```

## Required environment variables

```text
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_REDIRECT_URI
```

Default local redirect URI:

```text
http://127.0.0.1:8000/auth/github/callback
```

## Login flow

```text
1. User clicks Login with GitHub.
2. Ailovanta creates an OAuth state.
3. Ailovanta returns a GitHub authorization URL.
4. User authorizes on GitHub.
5. GitHub redirects to /auth/github/callback.
6. Ailovanta exchanges code for GitHub profile.
7. Ailovanta creates or updates local user.
8. Ailovanta creates local session token.
9. Client stores session token and sends it as Bearer token.
```

## Session usage

After login, the client uses:

```text
Authorization: Bearer sess_xxx
```

Then it can call:

```text
GET /auth/me
POST /auth/logout
```

## Current database tables

```text
auth_states
users
sessions
```

## What not to do yet

Do not add email/password.

Do not add magic email links.

Do not add phone login.

Do not add wallet login as the default account identity.

Do not add payment login.

Do not expose GitHub access tokens to the frontend.

Do not store GitHub access tokens unless there is a clear product need later.

## Future optional login methods

Only add these later if the product needs them:

```text
Email magic link
Google OAuth
Apple Sign In
Enterprise SSO
Wallet link for node operator rewards
```

For now, GitHub login is enough and keeps the MVP focused.
