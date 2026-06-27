from __future__ import annotations

from fastapi import APIRouter, Response

from api.alert_summary import AlertSummary


router = APIRouter()
alerts = AlertSummary()


def line(name: str, value: int | float, labels: dict[str, str] | None = None) -> str:
    if labels:
        inner = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{name}{{{inner}}} {value}"
    return f"{name} {value}"


@router.get("/metrics/alerts")
def alert_metrics() -> Response:
    status = alerts.collect()
    rows = [
        "# HELP ailovanta_alerts_ok Alert summary status",
        "# TYPE ailovanta_alerts_ok gauge",
        line("ailovanta_alerts_ok", 1 if status.get("ok") else 0),
        "# HELP ailovanta_alerts_total Alerts by severity",
        "# TYPE ailovanta_alerts_total gauge",
    ]
    for severity, count in status.get("levels", {}).items():
        rows.append(line("ailovanta_alerts_total", count, {"severity": str(severity)}))
    return Response("\n".join(rows) + "\n", media_type="text/plain; version=0.0.4")
