from pydantic import Field

from bridge.contracts.common import BridgeModel


class ConnectRequest(BridgeModel):
    attach_to_running: bool = True


class LaunchRequest(BridgeModel):
    exe_path: str | None = None
    visible: bool = True
    startup_delay_s: float = Field(default=3.0, ge=0.0, le=120.0)


class OpenModelRequest(BridgeModel):
    path: str
    copy_to_workspace: bool = False


class AnalysisRequest(BridgeModel):
    save_before_run: bool = False
    case_names: list[str] = Field(default_factory=list)
