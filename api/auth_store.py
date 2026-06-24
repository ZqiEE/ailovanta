from __future__ import annotations

import secrets
import sqlite3
import time
from pathlib import Path

from api.sqlite_utils import connect_sqlite


class AuthStore:
    def __init__(self, path: str | Path = "runtime_data/auth.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS auth_states (
                    state TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    consumed_at REAL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    github_id TEXT UNIQUE NOT NULL,
                    github_login TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    avatar_url TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    revoked_at REAL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                """
            )

    def create_state(self) -> str:
        state = secrets.token_urlsafe(32)
        with self.connect() as conn:
            conn.execute("INSERT INTO auth_states (state, created_at) VALUES (?, ?)", (state, time.time()))
        return state

    def consume_state(self, state: str, max_age_seconds: int = 600) -> bool:
        now = time.time()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM auth_states WHERE state = ?", (state,)).fetchone()
            if not row:
                return False
            if row["consumed_at"] is not None:
                return False
            if now - row["created_at"] > max_age_seconds:
                return False
            conn.execute("UPDATE auth_states SET consumed_at = ? WHERE state = ?", (now, state))
        return True

    def upsert_github_user(self, profile: dict) -> dict:
        now = time.time()
        github_id = str(profile["id"])
        github_login = profile["login"]
        user_id = f"usr_gh_{github_id}"
        with self.connect() as conn:
            existing = conn.execute("SELECT id FROM users WHERE github_id = ?", (github_id,)).fetchone()
            if existing:
                user_id = existing["id"]
                conn.execute(
                    "UPDATE users SET github_login = ?, name = ?, email = ?, avatar_url = ?, updated_at = ? WHERE id = ?",
                    (github_login, profile.get("name"), profile.get("email"), profile.get("avatar_url"), now, user_id),
                )
            else:
                conn.execute(
                    "INSERT INTO users (id, github_id, github_login, name, email, avatar_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, github_id, github_login, profile.get("name"), profile.get("email"), profile.get("avatar_url"), now, now),
                )
        return self.get_user(user_id) or {}

    def get_user(self, user_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def create_session(self, user_id: str, ttl_seconds: int = 60 * 60 * 24 * 30) -> dict:
        token = f"sess_{secrets.token_urlsafe(32)}"
        now = time.time()
        expires_at = now + ttl_seconds
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, user_id, now, expires_at),
            )
        return {"token": token, "user_id": user_id, "expires_at": expires_at}

    def get_session(self, token: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE token = ? AND revoked_at IS NULL AND expires_at > ?",
                (token, time.time()),
            ).fetchone()
        return dict(row) if row else None

    def revoke_session(self, token: str) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT token FROM sessions WHERE token = ?", (token,)).fetchone()
            if not row:
                return False
            conn.execute("UPDATE sessions SET revoked_at = ? WHERE token = ?", (time.time(), token))
        return True

    def status(self) -> dict:
        with self.connect() as conn:
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(*) FROM sessions WHERE revoked_at IS NULL AND expires_at > ?", (time.time(),)).fetchone()[0]
        return {"users": users, "active_sessions": sessions, "store": "sqlite", "path": str(self.path)}
