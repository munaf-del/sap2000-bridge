from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class BridgeError(Exception):
    http_status: int
    bridge_code: str
    message: str
    sap_ret: int | None = None
    sap_context: str | None = None
    retryable: bool = False


class NotConnectedError(BridgeError):
    def __init__(self) -> None:
        super().__init__(
            http_status=409,
            bridge_code="NOT_CONNECTED",
            message="SAP2000 is not connected. Call /sap2000/connect or /sap2000/launch first.",
            retryable=True,
        )


class NoModelOpenError(BridgeError):
    def __init__(self) -> None:
        super().__init__(
            http_status=409,
            bridge_code="NO_MODEL_OPEN",
            message="No SAP2000 model is open. Call /sap2000/open-model first.",
            retryable=False,
        )


def error_envelope(error: BridgeError, correlation_id: str) -> dict[str, dict[str, object]]:
    return {
        "error": {
            "http_status": error.http_status,
            "bridge_code": error.bridge_code,
            "message": error.message,
            "sap_ret": error.sap_ret,
            "sap_context": error.sap_context,
            "retryable": error.retryable,
            "correlation_id": correlation_id,
        }
    }


async def bridge_error_handler(request: Request, exc: BridgeError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    return JSONResponse(
        status_code=exc.http_status,
        content=error_envelope(exc, correlation_id),
    )
