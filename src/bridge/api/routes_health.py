from fastapi import APIRouter, Request

from bridge.config import get_settings
from bridge.contracts.model import BridgeInfo, HealthResponse
from bridge.services.install_validator import inspect_sap2000_target

router = APIRouter()

SUPPORTED_ENDPOINTS = [
    "GET /health",
    "GET /bridge/info",
    "GET /sap2000/status",
    "POST /sap2000/connect",
    "POST /sap2000/launch",
    "POST /sap2000/open-model",
    "GET /sap2000/model/units",
    "GET /sap2000/model/joints",
    "POST /sap2000/analyze",
    "POST /sap2000/analyse",
    "GET /sap2000/results/joint-reactions",
]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(ok=True, service=settings.service_name, version=settings.bridge_version)


@router.get("/bridge/info", response_model=BridgeInfo)
def bridge_info(request: Request) -> BridgeInfo:
    settings = get_settings()
    return BridgeInfo(
        bridge_version=settings.bridge_version,
        adapter_mode=settings.adapter_mode,
        read_only=settings.read_only,
        writeback_enabled=settings.writeback_enabled,
        supported_endpoints=SUPPORTED_ENDPOINTS,
        sap2000_target=inspect_sap2000_target(settings),
        correlation_id=request.state.correlation_id,
    )
