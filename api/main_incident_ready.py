from __future__ import annotations

from api.incident_routes import router as incident_router
from api.main_monitor_ready import app

app.include_router(incident_router)
