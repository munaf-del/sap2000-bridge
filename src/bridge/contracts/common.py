from pydantic import BaseModel, ConfigDict


class BridgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UnitsInfo(BridgeModel):
    # VERIFY AGAINST INSTALLED SAP2000 API CHM AND SAP2000v1.tlb before mapping
    # SAP2000 eUnits values into these stable strings.
    present: str
    database: str
    present_raw: int | str | None = None
    database_raw: int | str | None = None
    length: str
    force: str
    moment: str
    temperature: str | None = None
    mass: str | None = None
    time: str | None = None


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
