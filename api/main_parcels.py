from __future__ import annotations

from api.main_owned import app
from api.parcel_api import router as parcel_router

app.include_router(parcel_router)
