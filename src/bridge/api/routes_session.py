from fastapi import APIRouter, Request

from bridge.contracts.model import OpenModelResponse, SapSessionInfo, SapStatusResponse
from bridge.contracts.requests import ConnectRequest, LaunchRequest, OpenModelRequest
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000")


@router.get("/status", response_model=SapStatusResponse)
def status(request: Request) -> SapStatusResponse:
    return session_manager.status(correlation_id=request.state.correlation_id)


@router.post("/connect", response_model=SapSessionInfo)
def connect(payload: ConnectRequest, request: Request) -> SapSessionInfo:
    return session_manager.connect(payload=payload, correlation_id=request.state.correlation_id)


@router.post("/launch", response_model=SapSessionInfo)
def launch(payload: LaunchRequest, request: Request) -> SapSessionInfo:
    return session_manager.launch(payload=payload, correlation_id=request.state.correlation_id)


@router.post("/open-model", response_model=OpenModelResponse)
def open_model(payload: OpenModelRequest, request: Request) -> OpenModelResponse:
    return session_manager.open_model(payload=payload, correlation_id=request.state.correlation_id)
