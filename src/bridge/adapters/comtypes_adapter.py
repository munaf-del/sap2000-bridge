import sys

from bridge.adapters.base import SapAdapter
from bridge.config import Settings, get_settings
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import (
    FrameListResponse,
    JointListResponse,
    LoadCaseListResponse,
    LoadCombinationListResponse,
    LoadPatternListResponse,
    MaterialListResponse,
    OpenModelResponse,
    SapSessionInfo,
    SapStatusResponse,
    SectionListResponse,
)
from bridge.contracts.results import AnalysisJobStatus, JointReactionSet
from bridge.errors import BridgeError

if sys.platform == "win32":  # pragma: no cover - comtypes is optional and not used in automated tests.
    try:
        import comtypes.client as comtypes_client
    except ImportError:
        comtypes_client = None
else:  # pragma: no cover - keeps non-Windows imports clean.
    comtypes_client = None


VERIFY_CHM = "VERIFY AGAINST INSTALLED SAP2000 API CHM"
VERIFY_TLB = "VERIFY AGAINST SAP2000v1.tlb"
VERIFY_COMTYPES = "VERIFY comtypes tuple/byref behaviour on target machine"
VERIFY_ALL = f"{VERIFY_CHM}; {VERIFY_TLB}; {VERIFY_COMTYPES}"


def check_ret(ret: int | None, operation: str, sap_context: str | None = None) -> None:
    """Normalize every SAP2000 return code before callers see it."""
    if ret not in (None, 0):
        context = sap_context or operation
        raise BridgeError(
            http_status=502,
            bridge_code="SAP2000_RETURN_CODE",
            message=f"SAP2000 API call failed during {operation}.",
            sap_ret=ret,
            sap_context=context,
            retryable=False,
        )


class ComtypesSapAdapter(SapAdapter):
    """Placeholder adapter for future verified SAP2000 OAPI integration.

    All API-sensitive calls below must be checked against the installed SAP2000
    CHM/TLB/DLL on the target machine before they are implemented.
    """

    adapter_mode = "comtypes"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self.helper_progid = "SAP2000v1.Helper"
        self.csi_helper_progid = "CSiAPIv1.Helper"
        self.sap_object_progid = "CSI.SAP2000.API.SapObject"
        self.install_dir = self._settings.sap2000_install_dir
        self.exe_path = self._settings.sap2000_exe_path
        self.api_dll_path = self._settings.sap2000_api_dll_path
        self.csi_api_dll_path = self._settings.csi_api_dll_path
        self.oapi_chm_path = self._settings.sap2000_oapi_chm_path
        if comtypes_client is None:
            raise BridgeError(
                http_status=503,
                bridge_code="ADAPTER_UNAVAILABLE",
                message=(
                    "ComtypesSapAdapter is unavailable because comtypes is not installed or this is not Windows. "
                    "Use the fake adapter or install the Windows-only sap2000 optional extra."
                ),
                retryable=True,
            )
        self._helper = None
        self._sap_object = None
        self._sap_model = None

    def create_helper(self) -> object:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("create_helper")

    def attach_to_running(self) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("attach_to_running")

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        if attach_to_running:
            return self.attach_to_running()
        raise self._placeholder("connect")

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("launch")

    def get_version(self) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("get_version")

    def status(self) -> SapStatusResponse:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("status")

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("open_model")

    def get_units(self) -> UnitsInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("get_units")

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_joints")

    def list_frames(self, csys: str = "Global") -> FrameListResponse:
        # Likely call family: FrameObj.GetAllFrames or fallback FrameObj.GetNameList +
        # FrameObj.GetPoints + FrameObj.GetSection.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_frames")

    def list_materials(self) -> MaterialListResponse:
        # Likely call family: PropMaterial.GetNameList / GetMaterial.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_materials")

    def list_sections(self) -> SectionListResponse:
        # Likely call family: PropFrame.GetNameList.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_sections")

    def list_load_patterns(self) -> LoadPatternListResponse:
        # Likely call family: LoadPatterns.GetNameList / GetLoadType.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_patterns")

    def list_load_cases(self) -> LoadCaseListResponse:
        # Likely call family: LoadCases.GetNameList / GetTypeOAPI.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_cases")

    def list_load_combinations(self) -> LoadCombinationListResponse:
        # Likely call family: RespCombo.GetNameList / GetCaseList / GetTypeCombo.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_combinations")

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("run_analysis")

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("extract_joint_reactions")

    @staticmethod
    def _placeholder(operation: str) -> BridgeError:
        return BridgeError(
            http_status=501,
            bridge_code="SAP2000_COM_PLACEHOLDER",
            message=f"ComtypesSapAdapter.{operation} is a placeholder. {VERIFY_ALL}.",
            retryable=False,
        )
