from datetime import datetime, timezone
from typing import Any


def audit_event(action: str, correlation_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an audit-ready event object.

    Durable audit storage is deferred until write-back and real SAP2000 control
    are implemented.
    """
    return {
        "action": action,
        "correlation_id": correlation_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
