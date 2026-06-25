from api.node_registry_api import router


def test_nr_routes() -> None:
    assert any(route.path == "/node-registry/register" for route in router.routes)
