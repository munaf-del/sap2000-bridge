from datetime import datetime
from typing import Literal
from pydantic import Field

from bridge.contracts.common import BridgeModel, UnitsInfo


class AnalysisJobStatus(BridgeModel):
    job_id: str
    state: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    submitted_at_utc: datetime
    started_at_utc: datetime | None = None
    finished_at_utc: datetime | None = None
    case_status: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None
    correlation_id: str = ""


class JointReactionRow(BridgeModel):
    obj: str
    elm: str
    load_case: str
    step_type: str
    step_num: float
    f1: float
    f2: float
    f3: float
    m1: float
    m2: float
    m3: float


class ResultSetResponse(BridgeModel):
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    units: UnitsInfo
    correlation_id: str = ""


class JointReactionSetResponse(ResultSetResponse):
    rows: list[JointReactionRow] = Field(default_factory=list)


JointReactionSet = JointReactionSetResponse


class FrameForceRow(BridgeModel):
    obj: str
    obj_station: float
    elm: str
    elm_station: float
    load_case: str
    step_type: str
    step_num: float
    p: float
    v2: float
    v3: float
    t: float
    m2: float
    m3: float


class FrameForceSetResponse(ResultSetResponse):
    rows: list[FrameForceRow] = Field(default_factory=list)


class ModalPeriodRow(BridgeModel):
    load_case: str
    step_type: str
    step_num: float
    period: float
    frequency: float
    circular_frequency: float
    eigenvalue: float


class ModalPeriodSetResponse(ResultSetResponse):
    rows: list[ModalPeriodRow] = Field(default_factory=list)
