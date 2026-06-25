from __future__ import annotations

from api.main_owned import app
from api.parcel_routes import router

app.include_router(router)
