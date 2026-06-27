from __future__ import annotations

from api.backup_routes import router as bk
from api.main_abuse_ready import app

app.include_router(bk)
