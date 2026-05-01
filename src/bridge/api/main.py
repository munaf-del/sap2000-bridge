from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from bridge.config import get_settings
from bridge.errors import BridgeError, bridge_error_handler
from bridge.logging import configure_logging
from bridge.api.routes_analysis import router as analysis_router
from bridge.api.routes_health import router as health_router
from bridge.api.routes_model import router as model_router
from bridge.api.routes_results import router as results_router
from bridge.api.routes_session import router as session_router

configure_logging()
settings = get_settings()

app = FastAPI(
    title="SAP2000 Local Bridge",
    version=settings.bridge_version,
    description="Local read-only bridge for SAP2000 automation through approved endpoints.",
)

app.add_exception_handler(BridgeError, bridge_error_handler)

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
    return response


app.include_router(health_router)
app.include_router(session_router)
app.include_router(model_router)
app.include_router(analysis_router)
app.include_router(results_router)
