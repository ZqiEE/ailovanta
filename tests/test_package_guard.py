from __future__ import annotations

from api.model_package import build_model_package
from api.protected_model_package import build_protected_package


def test_package_guard_has_policy_hash() -> None:
    package = build_model_package("demo", "v1", "base", "a", "d", 0.9, "obj")
    guarded = build_protected_package(package, "protected", {"required": 2, "total": 3}, "obj2")
    assert guarded["package_hash"] == package["package_hash"]
    assert guarded["policy_hash"]
