from fastapi import APIRouter, Request

from bridge.contracts.model import OpenModelResponse, SapSessionInfo, SapStatus
from bridge.contracts.requests import ConnectRequest, LaunchRequest, OpenModelRequest
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000")


@router.get("/status", response_model=SapStatus)
def status(request: Request) -> SapStatus:
    response = session_manager.adapter.status()
    response.correlation_id = request.state.correlation_id
    return response


@router.post("/connect", response_model=SapSessionInfo)
def connect(payload: ConnectRequest, request: Request) -> SapSessionInfo:
    response = session_manager.adapter.connect(attach_to_running=payload.attach_to_running)
    response.correlation_id = request.state.correlation_id
    return response


@router.post("/launch", response_model=SapSessionInfo)
def launch(payload: LaunchRequest, request: Request) -> SapSessionInfo:
    response = session_manager.adapter.launch(
        exe_path=payload.exe_path,
        visible=payload.visible,
        startup_delay_s=payload.startup_delay_s,
    )
    response.correlation_id = request.state.correlation_id
    return response


@router.post("/open-model", response_model=OpenModelResponse)
def open_model(payload: OpenModelRequest, request: Request) -> OpenModelResponse:
    response = session_manager.adapter.open_model(
        path=payload.path,
        copy_to_workspace=payload.copy_to_workspace,
    )
    response.correlation_id = request.state.correlation_id
    return response
