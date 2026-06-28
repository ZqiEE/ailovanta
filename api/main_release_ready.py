from __future__ import annotations

from api.default_chat_probe_routes import router as default_chat_probe_router
from api.final_gate_routes import router as final_gate_router
from api.main_incident_ready import app
from api.result_guard_routes import router as result_guard_router

app.include_router(final_gate_router)
app.include_router(default_chat_probe_router)
app.include_router(result_guard_router)
