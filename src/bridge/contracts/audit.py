from datetime import datetime
from pydantic import Field

from bridge.contracts.common import BridgeModel


class AuditRecord(BridgeModel):
    audit_id: str
    timestamp_utc: datetime
    correlation_id: str
    method: str
    route: str
    action: str
    status: str
    adapter_mode: str
    model_path: str | None = None
    bridge_code: str | None = None
    sap_ret: int | None = None


class AuditListResponse(BridgeModel):
    records: list[AuditRecord] = Field(default_factory=list)
    correlation_id: str


class AuditRecordResponse(BridgeModel):
    record: AuditRecord
    correlation_id: str
