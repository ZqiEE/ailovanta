from __future__ import annotations

from dataclasses import dataclass


LEVEL_ORDER = {"public": 0, "network": 1, "protected": 2, "confidential": 3, "core": 4}


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    level: str
    reason: str


class ModelAccessPolicy:
    def __init__(self, default_level: str = "protected") -> None:
        self.default_level = default_level

    def decide(self, model_level: str | None, node: dict, task: dict | None = None) -> AccessDecision:
        level = model_level or self.default_level
        if level not in LEVEL_ORDER:
            return AccessDecision(False, level, "unknown model level")

        if level == "public":
            return AccessDecision(True, level, "public model")

        if level == "network":
            if float(node.get("reputation", 0)) >= 0.2:
                return AccessDecision(True, level, "network reputation accepted")
            return AccessDecision(False, level, "network reputation too low")

        if level == "protected":
            if float(node.get("reputation", 0)) >= 0.5 and float(node.get("stake", 0)) >= 1:
                return AccessDecision(True, level, "protected node accepted")
            return AccessDecision(False, level, "protected model requires reputation and stake")

        if level == "confidential":
            if node.get("attested") is True and float(node.get("reputation", 0)) >= 0.7 and float(node.get("stake", 0)) >= 5:
                return AccessDecision(True, level, "confidential node accepted")
            return AccessDecision(False, level, "confidential model requires attestation reputation and stake")

        if level == "core":
            if node.get("core_node") is True and node.get("attested") is True:
                return AccessDecision(True, level, "core node accepted")
            return AccessDecision(False, level, "core model only runs on core attested nodes")

        return AccessDecision(False, level, "denied")
