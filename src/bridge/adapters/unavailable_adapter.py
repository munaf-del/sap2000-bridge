from bridge.adapters.base import SapAdapter
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import JointListResponse, OpenModelResponse, SapSessionInfo, SapStatusResponse
from bridge.contracts.results import AnalysisJobStatus, JointReactionSet
from bridge.errors import BridgeError


class UnavailableSapAdapter(SapAdapter):
    adapter_mode = "unavailable"

    def __init__(self, requested_mode: str, error: BridgeError) -> None:
        self.requested_mode = requested_mode
        self.adapter_mode = requested_mode
        self._error = error

    def status(self) -> SapStatusResponse:
        return SapStatusResponse(
            connected=False,
            launched_by_bridge=False,
            model_open=False,
            model_path=None,
            model_name=None,
            version_label=None,
            version_number=None,
            adapter_mode=self.adapter_mode,
            correlation_id="",
        )

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        raise self._error

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        raise self._error

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        raise self._error

    def get_units(self) -> UnitsInfo:
        raise self._error

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        raise self._error

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        raise self._error

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        raise self._error
