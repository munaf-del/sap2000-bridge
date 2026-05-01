from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from bridge.config import get_settings
from bridge.errors import BridgeError, bridge_error_handler, http_error_handler, validation_error_handler
from bridge.logging import configure_logging
from bridge.api.routes_analysis import router as analysis_router
from bridge.api.routes_audit import router as audit_router
from bridge.api.routes_health import router as health_router
from bridge.api.routes_model import router as model_router
from bridge.api.routes_results import router as results_router
from bridge.api.routes_session import router as session_router
from bridge.api.routes_writeback import router as writeback_router

configure_logging()
settings = get_settings()

app = FastAPI(
    title="SAP2000 Local Bridge",
    version=settings.bridge_version,
    description="Local read-only bridge for SAP2000 automation through approved endpoints.",
)

app.add_exception_handler(BridgeError, bridge_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    request.state.correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    _audit_request(request=request, status_code=response.status_code, response_headers=response.headers)
    return response


def _audit_request(request: Request, status_code: int, response_headers) -> None:
    from bridge.services.audit import audit_service
    from bridge.services.session_manager import session_manager

    try:
        adapter_status = session_manager.adapter.status()
        adapter_mode = adapter_status.adapter_mode
        model_path = adapter_status.model_path
    except Exception:
        adapter_mode = getattr(session_manager.adapter, "adapter_mode", "unknown")
        model_path = None
    route = getattr(request.scope.get("route"), "path", request.url.path)
    bridge_code = response_headers.get("X-Bridge-Code")
    sap_ret_header = response_headers.get("X-Sap-Ret")
    try:
        audit_service.record(
            correlation_id=request.state.correlation_id,
            method=request.method,
            route=route,
            action=f"{request.method} {route}",
            status="succeeded" if status_code < 400 else "failed",
            adapter_mode=adapter_mode,
            model_path=model_path,
            bridge_code=bridge_code,
            sap_ret=int(sap_ret_header) if sap_ret_header else None,
        )
    except Exception:
        pass


app.include_router(health_router)
app.include_router(session_router)
app.include_router(model_router)
app.include_router(analysis_router)
app.include_router(results_router)
app.include_router(writeback_router)
app.include_router(audit_router)
