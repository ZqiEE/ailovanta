from __future__ import annotations

from api.main import app
from api.owned_doctor import OwnedDoctor


@app.get("/diag/owned")
def diag_owned(model_key: str = "ailovanta-owned:candidate") -> dict:
    return OwnedDoctor().check(model_key)
