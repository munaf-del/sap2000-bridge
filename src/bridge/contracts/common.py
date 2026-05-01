from pydantic import BaseModel, ConfigDict


class BridgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UnitsInfo(BridgeModel):
    present: str
    database: str
    length: str
    force: str
    moment: str


class ApiError(BridgeModel):
    http_status: int
    bridge_code: str
    message: str
    sap_ret: int | None
    sap_context: str | None
    retryable: bool
    correlation_id: str


class ErrorEnvelope(BridgeModel):
    error: ApiError
