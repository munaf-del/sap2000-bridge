from datetime import datetime, timezone
from uuid import uuid4

from bridge.contracts.audit import AuditRecord
from bridge.errors import BridgeError


class AuditService:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(
        self,
        correlation_id: str,
        method: str,
        route: str,
        action: str,
        status: str,
        adapter_mode: str,
        model_path: str | None = None,
        bridge_code: str | None = None,
        sap_ret: int | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            audit_id=f"audit-{uuid4()}",
            timestamp_utc=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            method=method,
            route=route,
            action=action,
            status=status,
            adapter_mode=adapter_mode,
            model_path=model_path,
            bridge_code=bridge_code,
            sap_ret=sap_ret,
        )
        self._records.append(record)
        return record

    def list_records(self) -> list[AuditRecord]:
        return list(self._records)

    def get_record(self, audit_id: str) -> AuditRecord:
        for record in self._records:
            if record.audit_id == audit_id:
                return record
        raise BridgeError(
            http_status=404,
            bridge_code="UNKNOWN_AUDIT_RECORD",
            message=f"Audit record was not found: {audit_id}",
            retryable=False,
        )

    def clear(self) -> None:
        self._records.clear()


audit_service = AuditService()
