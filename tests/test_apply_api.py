from api.apply_api import router


def test_apply_route_exists() -> None:
    paths = [route.path for route in router.routes]
    assert "/apply/result" in paths
