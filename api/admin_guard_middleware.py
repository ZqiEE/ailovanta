from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse


SENSITIVE_PREFIXES = ("/ops", "/node-keys", "/objects", "/artifacts", "/adapters")


def install_admin_guard(app) -> None:
    @app.middleware("http")
    async def admin_guard(request: Request, call_next: Callable[[Request], Awaitable]):
        expected = os.environ.get("AILOVANTA_ADMIN_TOKEN", "")
        if expected and request.url.path.startswith(SENSITIVE_PREFIXES):
            supplied = request.headers.get("X-Ailovanta-Admin-Token", "")
            if not hmac.compare_digest(supplied, expected):
                return JSONResponse({"detail": "admin token required"}, status_code=401)
        return await call_next(request)
