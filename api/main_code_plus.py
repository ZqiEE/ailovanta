from __future__ import annotations

from api.main_code import app
from api.route_health_api import router as route_health_router

app.include_router(route_health_router)
