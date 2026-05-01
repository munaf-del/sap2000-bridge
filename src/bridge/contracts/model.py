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
    version_number: float | str | None
    adapter_mode: str
    correlation_id: str


class SapSessionInfo(BridgeModel):
    connected: bool
    launched_by_bridge: bool
    version_label: str
    version_number: float | str
    adapter_mode: str
    correlation_id: str = ""


class OpenModelResponse(BridgeModel):
    model_open: bool
    model_path: str
    model_name: str
    version_label: str
    version_number: float | str
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
    version_number: float | str
    adapter_mode: str
    units: UnitsInfo
    joints: list[JointInfo] = Field(default_factory=list)
    correlation_id: str = ""


class UnitsResponse(BridgeModel):
    model_path: str
    model_name: str
    version_label: str
    version_number: float | str
    adapter_mode: str
    units: UnitsInfo
    correlation_id: str


class ModelMetadataResponse(BridgeModel):
    model_path: str
    model_name: str
    version_label: str
    version_number: float | str
    adapter_mode: str
    units: UnitsInfo
    correlation_id: str = ""


class Frame(BridgeModel):
    name: str
    start_joint: str | None = None
    end_joint: str | None = None
    section: str | None = None
    coord_system: str


class FrameListResponse(ModelMetadataResponse):
    frames: list[Frame] = Field(default_factory=list)


class Material(BridgeModel):
    name: str
    material_type: str | int | None = None


class MaterialListResponse(ModelMetadataResponse):
    materials: list[Material] = Field(default_factory=list)


class FrameSection(BridgeModel):
    name: str
    shape_type: str | None = None
    material: str | None = None


class SectionListResponse(ModelMetadataResponse):
    sections: list[FrameSection] = Field(default_factory=list)


class LoadPattern(BridgeModel):
    name: str
    load_type: str | int | None = None
    self_weight_multiplier: float | None = None


class LoadPatternListResponse(ModelMetadataResponse):
    load_patterns: list[LoadPattern] = Field(default_factory=list)


class LoadCase(BridgeModel):
    name: str
    case_type: str | int | None = None


class LoadCaseListResponse(ModelMetadataResponse):
    load_cases: list[LoadCase] = Field(default_factory=list)


class LoadCombinationItem(BridgeModel):
    name: str
    scale_factor: float | None = None


class LoadCombination(BridgeModel):
    name: str
    items: list[LoadCombinationItem] = Field(default_factory=list)


class LoadCombinationListResponse(ModelMetadataResponse):
    load_combinations: list[LoadCombination] = Field(default_factory=list)
