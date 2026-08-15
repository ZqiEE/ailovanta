from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class WeightedMetric:
    name: str
    weight: float


DOMAIN_METRICS: dict[str, tuple[WeightedMetric, ...]] = {
    "frontend": (
        WeightedMetric("browser_render", 0.15),
        WeightedMetric("visual_quality", 0.30),
        WeightedMetric("interaction_success", 0.25),
        WeightedMetric("responsive_quality", 0.15),
        WeightedMetric("accessibility", 0.15),
    ),
    "backend": (
        WeightedMetric("build_success", 0.15),
        WeightedMetric("unit_tests", 0.20),
        WeightedMetric("integration_tests", 0.30),
        WeightedMetric("api_contracts", 0.15),
        WeightedMetric("database_checks", 0.10),
        WeightedMetric("regression_free", 0.10),
    ),
    "repair": (
        WeightedMetric("bug_reproduced", 0.10),
        WeightedMetric("root_cause_localized", 0.15),
        WeightedMetric("failing_test_fixed", 0.35),
        WeightedMetric("regression_suite", 0.25),
        WeightedMetric("patch_minimality", 0.15),
    ),
}


class CodingBenchmarkError(ValueError):
    pass


def _score_value(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def score_domain(domain: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    if domain not in DOMAIN_METRICS:
        raise CodingBenchmarkError(f"unknown coding benchmark domain: {domain}")

    details: list[dict[str, Any]] = []
    score = 0.0
    for metric in DOMAIN_METRICS[domain]:
        value = _score_value(metrics.get(metric.name, 0.0))
        contribution = value * metric.weight
        score += contribution
        details.append(
            {
                "metric": metric.name,
                "value": round(value, 4),
                "weight": metric.weight,
                "contribution": round(contribution, 4),
            }
        )

    final = round(score, 4)
    return {
        "domain": domain,
        "score": final,
        "passed": final >= 0.70,
        "promotion_ready": final >= 0.80,
        "details": details,
    }


def score_unified(frontend: float, backend: float, repair: float) -> dict[str, Any]:
    scores = {
        "frontend": _score_value(frontend),
        "backend": _score_value(backend),
        "repair": _score_value(repair),
    }
    # The unified model must not hide a weak specialist behind a strong average.
    floor = min(scores.values())
    average = sum(scores.values()) / len(scores)
    final = round((0.6 * floor) + (0.4 * average), 4)
    weakest = min(scores, key=scores.get)
    return {
        "score": final,
        "domain_scores": {key: round(value, 4) for key, value in scores.items()},
        "weakest_domain": weakest,
        "passed": floor >= 0.70 and average >= 0.75,
        "promotion_ready": floor >= 0.80 and average >= 0.85,
    }
