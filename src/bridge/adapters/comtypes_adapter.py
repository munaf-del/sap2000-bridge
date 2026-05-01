from bridge.adapters.base import SapAdapter
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import JointListResponse, OpenModelResponse, SapSessionInfo, SapStatusResponse
from bridge.contracts.results import AnalysisJobStatus, JointReactionSet
from bridge.errors import BridgeError

try:  # pragma: no cover - SAP2000/comtypes is intentionally optional for tests.
    import comtypes.client as comtypes_client
except ImportError:  # pragma: no cover
    comtypes_client = None


VERIFY_CHM = "VERIFY AGAINST INSTALLED SAP2000 API CHM"
VERIFY_COMTYPES = "VERIFY comtypes tuple/byref behaviour on target machine"


def check_ret(ret: int | None, context: str) -> None:
    """Normalize every SAP2000 return code before callers see it."""
    if ret not in (None, 0):
        raise BridgeError(
            http_status=502,
            bridge_code="SAP2000_RETURN_CODE",
            message=f"SAP2000 API call failed during {context}.",
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

    def __init__(self) -> None:
        if comtypes_client is None:
            raise BridgeError(
                http_status=503,
                bridge_code="COMTYPES_UNAVAILABLE",
                message="comtypes is not installed. Use the fake adapter or install the sap2000 optional extra.",
                retryable=True,
            )
        self._helper = None
        self._sap_object = None
        self._sap_model = None

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        # helper creation: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # attach to running SAP2000: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # get version: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("connect")

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        # helper creation: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # create/launch SAP2000: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # get version: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("launch")

    def status(self) -> SapStatusResponse:
        # get version/model state: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("status")

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        # open model: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # get present units: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # get database units: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("open_model")

    def get_units(self) -> UnitsInfo:
        # get present units: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # get database units: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("get_units")

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        # list joints: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_joints")

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        # run analysis: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("run_analysis")

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        # extract joint reactions: VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("extract_joint_reactions")

    @staticmethod
    def _placeholder(operation: str) -> BridgeError:
        return BridgeError(
            http_status=501,
            bridge_code="SAP2000_COM_PLACEHOLDER",
            message=(
                f"ComtypesSapAdapter.{operation} is a placeholder. {VERIFY_CHM}; "
                f"{VERIFY_COMTYPES}."
            ),
            retryable=False,
        )
