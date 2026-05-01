from typing import Protocol

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


class SapAdapter(Protocol):
    adapter_mode: str

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        ...

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        ...

    def status(self) -> SapStatusResponse:
        ...

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        ...

    def get_units(self) -> UnitsInfo:
        ...

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        ...

    def list_frames(self, csys: str = "Global") -> FrameListResponse:
        ...

    def list_materials(self) -> MaterialListResponse:
        ...

    def list_sections(self) -> SectionListResponse:
        ...

    def list_load_patterns(self) -> LoadPatternListResponse:
        ...

    def list_load_cases(self) -> LoadCaseListResponse:
        ...

    def list_load_combinations(self) -> LoadCombinationListResponse:
        ...

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        ...

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        ...
