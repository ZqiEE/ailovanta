from __future__ import annotations

from api.main import app
from api.node_registry_api import router as nr_router

app.include_router(nr_router)
