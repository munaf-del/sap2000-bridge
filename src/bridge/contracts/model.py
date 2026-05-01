from pydantic import Field

from bridge.contracts.common import BridgeModel, UnitsInfo


class HealthResponse(BridgeModel):
    ok: bool = True
    service: str
    version: str


class BridgeInfo(BridgeModel):
    bridge_version: str
    adapter_mode: str
    read_only: bool
    writeback_enabled: bool
    supported_endpoints: list[str]
    sap2000_target: "Sap2000TargetInfo"
    correlation_id: str


class Sap2000TargetInfo(BridgeModel):
    configured_version: str | None
    install_dir: str | None
    exe_path: str | None
    api_dll_path: str | None
    csi_api_dll_path: str | None
    oapi_chm_path: str | None
    sap2000_chm_path: str | None
    native_api_dir: str | None
    register_tool_path: str | None
    install_dir_present: bool
    exe_present: bool
    api_dll_present: bool
    csi_api_dll_present: bool
    oapi_chm_present: bool
    sap2000_chm_present: bool
    native_api_dir_present: bool
    register_tool_present: bool
    all_required_present: bool
    sap2000_helper_progid_registered: bool
    csi_helper_progid_registered: bool
    sap_object_progid_registered: bool
    com_registration_ready: bool


class SapStatus(BridgeModel):
    connected: bool
    model_open: bool
    model_path: str | None
    version_label: str | None
    adapter_mode: str
    correlation_id: str


class SapSessionInfo(BridgeModel):
    connected: bool
    version_label: str
    version_number: str
    adapter_mode: str
    correlation_id: str = ""


class OpenModelResponse(BridgeModel):
    model_open: bool
    model_path: str
    model_name: str
    units: UnitsInfo
    correlation_id: str = ""


class JointRestraint(BridgeModel):
    u1: bool = False
    u2: bool = False
    u3: bool = False
    r1: bool = False
    r2: bool = False
    r3: bool = False


class JointInfo(BridgeModel):
    name: str
    coord_system: str
    x: float
    y: float
    z: float
    units_ref: str
    restraint: JointRestraint | None = None


class JointListResponse(BridgeModel):
    model_path: str
    version_label: str
    units: UnitsInfo
    joints: list[JointInfo] = Field(default_factory=list)
    correlation_id: str = ""
