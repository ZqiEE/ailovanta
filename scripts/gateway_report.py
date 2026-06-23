from __future__ import annotations

import json

from api.gateway_audit_log import GatewayAuditLog
from api.gateway_status import gateway_status


def main() -> None:
    audit = GatewayAuditLog()
    report = {"status": gateway_status(), "events": audit.list_events(limit=20)}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
