from fastapi import APIRouter, Request

from bridge.contracts.audit import AuditListResponse, AuditRecordResponse
from bridge.services.audit import audit_service

router = APIRouter(prefix="/sap2000/audit")


@router.get("", response_model=AuditListResponse)
def list_audit_records(request: Request) -> AuditListResponse:
    return AuditListResponse(records=audit_service.list_records(), correlation_id=request.state.correlation_id)


@router.get("/{audit_id}", response_model=AuditRecordResponse)
def get_audit_record(audit_id: str, request: Request) -> AuditRecordResponse:
    return AuditRecordResponse(
        record=audit_service.get_record(audit_id),
        correlation_id=request.state.correlation_id,
    )
