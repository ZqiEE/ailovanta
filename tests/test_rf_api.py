from api.rflow_api import router


def test_route() -> None:
    paths = [r.path for r in router.routes]
    assert "/rflow/run" in paths
