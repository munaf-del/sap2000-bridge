from dataclasses import dataclass

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


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


class InvalidModelPathError(BridgeError):
    def __init__(self, path: str) -> None:
        super().__init__(
            http_status=400,
            bridge_code="INVALID_MODEL_PATH",
            message=f"Model path must point to a local .sdb file: {path}",
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


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    error = BridgeError(
        http_status=422,
        bridge_code="VALIDATION_ERROR",
        message=str(exc.errors()),
        retryable=False,
    )
    return JSONResponse(status_code=422, content=error_envelope(error, correlation_id))


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    error = BridgeError(
        http_status=exc.status_code,
        bridge_code="HTTP_ERROR",
        message=str(exc.detail),
        retryable=False,
    )
    return JSONResponse(status_code=exc.status_code, content=error_envelope(error, correlation_id))
