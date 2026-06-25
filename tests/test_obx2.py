from api.obx2_api import router
from api.outbox_run_v2 import run_from_payload_v2


def test_obx2_routes() -> None:
    paths = [route.path for route in router.routes]
    assert "/obx2/submit" in paths
    assert "/obx2/runs" in paths


def test_obx2_disabled() -> None:
    assert run_from_payload_v2({"id": "x"}) is None
