from pydantic import Field

from bridge.contracts.common import BridgeModel, UnitsInfo


class HealthResponse(BridgeModel):
    ok: bool = True
    service: str
    version: str
    correlation_id: str


class Sap2000TargetInfo(BridgeModel):
    configured_version: str | None
    configured_root: str | None
    install_dir: str | None
    exe_path: str | None
    sap2000v1_dll_path: str | None
    csiapiv1_dll_path: str | None
    csi_oapi_documentation_path: str | None
    sap2000_chm_path: str | None
    native_api_path: str | None
    register_sap2000_path: str | None


class InstallValidation(BridgeModel):
    configured_version: str | None
    configured_root: str | None
    sap2000_exe_present: bool
    sap2000v1_dll_present: bool
    csiapiv1_dll_present: bool
    csi_oapi_documentation_present: bool
    sap2000_chm_present: bool
    native_api_present: bool
    register_sap2000_present: bool
    all_required_present: bool
    com_registration_ready: bool
    helper_progids: dict[str, bool]
    sap_object_progid: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)


class BridgeInfoResponse(BridgeModel):
    bridge_version: str
    adapter_mode: str
    read_only: bool
    writeback_enabled: bool
    supported_endpoints: list[str]
    sap2000_target: Sap2000TargetInfo
    install_validation: InstallValidation
    correlation_id: str


class SapStatusResponse(BridgeModel):
    connected: bool
    launched_by_bridge: bool
    model_open: bool
    model_path: str | None
    model_name: str | None
    version_label: str | None
    version_number: str | None
    adapter_mode: str
    correlation_id: str


class SapSessionInfo(BridgeModel):
    connected: bool
    launched_by_bridge: bool
    version_label: str
    version_number: str
    adapter_mode: str
    correlation_id: str = ""


class OpenModelResponse(BridgeModel):
    model_open: bool
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
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
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    units: UnitsInfo
    joints: list[JointInfo] = Field(default_factory=list)
    correlation_id: str = ""


class UnitsResponse(BridgeModel):
    model_path: str
    model_name: str
    version_label: str
    version_number: str
    adapter_mode: str
    units: UnitsInfo
    correlation_id: str
