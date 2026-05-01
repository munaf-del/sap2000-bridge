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


class JointReactionSet(BridgeModel):
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    units: UnitsInfo
    rows: list[JointReactionRow] = Field(default_factory=list)
    correlation_id: str = ""
