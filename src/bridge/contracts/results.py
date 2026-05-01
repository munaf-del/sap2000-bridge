from datetime import datetime
from pydantic import Field

from bridge.contracts.common import BridgeModel, UnitsInfo


class AnalysisJobStatus(BridgeModel):
    job_id: str
    state: str
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    submitted_at_utc: datetime
    started_at_utc: datetime
    finished_at_utc: datetime
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
