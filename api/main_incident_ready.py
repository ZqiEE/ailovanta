from __future__ import annotations

from api.incident_routes import router as incident_router
from api.main_monitor_ready import app
from api.rollback_api import router as rollback_router

app.include_router(incident_router)
app.include_router(rollback_router)
