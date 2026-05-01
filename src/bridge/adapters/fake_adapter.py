from datetime import datetime, timezone
from pathlib import PureWindowsPath
from uuid import uuid4

from bridge.adapters.base import SapAdapter
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import (
    Frame,
    FrameListResponse,
    FrameSection,
    JointInfo,
    JointListResponse,
    JointRestraint,
    LoadCase,
    LoadCaseListResponse,
    LoadCombination,
    LoadCombinationItem,
    LoadCombinationListResponse,
    LoadPattern,
    LoadPatternListResponse,
    Material,
    MaterialListResponse,
    OpenModelResponse,
    SapSessionInfo,
    SapStatusResponse,
    SectionListResponse,
)
from bridge.contracts.results import AnalysisJobStatus, JointReactionRow, JointReactionSet
from bridge.errors import InvalidModelPathError, NoModelOpenError, NotConnectedError


class FakeSapAdapter(SapAdapter):
    adapter_mode = "fake"

    def __init__(self) -> None:
        self._connected = False
        self._launched_by_bridge = False
        self._model_path: str | None = None
        self._version_label = "SAP2000 Fake Adapter v0.1"
        self._version_number = "0.1.0-fake"
        self._units = UnitsInfo(
            present="kN_m_C",
            database="kN_m_C",
            length="m",
            force="kN",
            moment="kN-m",
            temperature="C",
        )

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        self._connected = True
        return SapSessionInfo(
            connected=True,
            launched_by_bridge=self._launched_by_bridge,
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
        )

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        self._connected = True
        self._launched_by_bridge = True
        return SapSessionInfo(
            connected=True,
            launched_by_bridge=True,
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
        )

    def status(self) -> SapStatusResponse:
        return SapStatusResponse(
            connected=self._connected,
            launched_by_bridge=self._launched_by_bridge,
            model_open=self._model_path is not None,
            model_path=self._model_path,
            model_name=self._model_name,
            version_label=self._version_label if self._connected else None,
            version_number=self._version_number if self._connected else None,
            adapter_mode=self.adapter_mode,
            correlation_id="",
        )

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        self._require_connected()
        if not path.lower().endswith(".sdb"):
            raise InvalidModelPathError(path)
        self._model_path = path
        return OpenModelResponse(
            model_open=True,
            model_path=path,
            model_name=self._model_name or PureWindowsPath(path).name,
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
            units=self._units,
        )

    def get_units(self) -> UnitsInfo:
        self._require_model()
        return self._units

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        self._require_model()
        joints = [
            JointInfo(name="J1", coord_system=csys, x=0.0, y=0.0, z=0.0, units_ref=self._units.length),
            JointInfo(name="J2", coord_system=csys, x=6.0, y=0.0, z=0.0, units_ref=self._units.length),
            JointInfo(name="J3", coord_system=csys, x=6.0, y=4.0, z=0.0, units_ref=self._units.length),
            JointInfo(name="J4", coord_system=csys, x=0.0, y=4.0, z=0.0, units_ref=self._units.length),
        ]
        if include_restraints:
            joints[0].restraint = JointRestraint(u1=True, u2=True, u3=True, r1=True, r2=True, r3=True)
            joints[1].restraint = JointRestraint(u1=True, u2=True, u3=True, r1=False, r2=False, r3=False)
        return JointListResponse(
            model_path=self._model_path or "",
            model_name=self._model_name or "",
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
            units=self._units,
            joints=joints,
        )

    def list_frames(self, csys: str = "Global") -> FrameListResponse:
        self._require_model()
        return FrameListResponse(
            **self._metadata_envelope(),
            frames=[
                Frame(name="F1", start_joint="P1", end_joint="P2", section="UB310", coord_system=csys),
                Frame(name="F2", start_joint="P2", end_joint="P3", section="UB310", coord_system=csys),
            ],
        )

    def list_materials(self) -> MaterialListResponse:
        self._require_model()
        return MaterialListResponse(
            **self._metadata_envelope(),
            materials=[
                Material(name="CONC32", material_type="Concrete"),
                Material(name="STEEL350", material_type="Steel"),
            ],
        )

    def list_sections(self) -> SectionListResponse:
        self._require_model()
        return SectionListResponse(
            **self._metadata_envelope(),
            sections=[
                FrameSection(name="UB310", shape_type="ISection", material="STEEL350"),
                FrameSection(name="SLAB150", shape_type="Shell/Slab", material="CONC32"),
            ],
        )

    def list_load_patterns(self) -> LoadPatternListResponse:
        self._require_model()
        return LoadPatternListResponse(
            **self._metadata_envelope(),
            load_patterns=[
                LoadPattern(name="DEAD", load_type="Dead", self_weight_multiplier=1.0),
                LoadPattern(name="LIVE", load_type="Live", self_weight_multiplier=0.0),
            ],
        )

    def list_load_cases(self) -> LoadCaseListResponse:
        self._require_model()
        return LoadCaseListResponse(
            **self._metadata_envelope(),
            load_cases=[
                LoadCase(name="DEAD", case_type="LinearStatic"),
                LoadCase(name="LIVE", case_type="LinearStatic"),
            ],
        )

    def list_load_combinations(self) -> LoadCombinationListResponse:
        self._require_model()
        return LoadCombinationListResponse(
            **self._metadata_envelope(),
            load_combinations=[
                LoadCombination(
                    name="ULS_1",
                    items=[
                        LoadCombinationItem(name="DEAD", scale_factor=1.2),
                        LoadCombinationItem(name="LIVE", scale_factor=1.5),
                    ],
                ),
                LoadCombination(
                    name="SLS_1",
                    items=[
                        LoadCombinationItem(name="DEAD", scale_factor=1.0),
                        LoadCombinationItem(name="LIVE", scale_factor=1.0),
                    ],
                ),
            ],
        )

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        self._require_model()
        now = datetime.now(timezone.utc)
        return AnalysisJobStatus(
            job_id=f"fake-analysis-{uuid4()}",
            state="completed",
            model_path=self._model_path or "",
            model_name=self._model_name or "",
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
            submitted_at_utc=now,
            started_at_utc=now,
            finished_at_utc=now,
        )

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        self._require_model()
        selected_cases = case_names or ["DEAD"]
        rows = [
            JointReactionRow(
                obj=point_name,
                elm=point_name,
                load_case=case_name,
                step_type="Max",
                step_num=0.0,
                f1=10.0,
                f2=0.0,
                f3=125.0,
                m1=0.0,
                m2=5.0,
                m3=0.0,
            )
            for case_name in selected_cases
        ]
        rows.extend(
            JointReactionRow(
                obj=point_name,
                elm=point_name,
                load_case=combo_name,
                step_type="Combo",
                step_num=0.0,
                f1=15.0,
                f2=0.0,
                f3=180.0,
                m1=0.0,
                m2=8.0,
                m3=0.0,
            )
            for combo_name in combo_names
        )
        return JointReactionSet(
            model_path=self._model_path or "",
            model_name=self._model_name or "",
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
            units=self._units,
            rows=rows,
        )

    @property
    def _model_name(self) -> str | None:
        return PureWindowsPath(self._model_path).name if self._model_path else None

    def _metadata_envelope(self) -> dict[str, object]:
        return {
            "model_path": self._model_path or "",
            "model_name": self._model_name or "",
            "version_label": self._version_label,
            "version_number": self._version_number,
            "adapter_mode": self.adapter_mode,
            "units": self._units,
        }

    def _require_connected(self) -> None:
        if not self._connected:
            raise NotConnectedError()

    def _require_model(self) -> None:
        self._require_connected()
        if self._model_path is None:
            raise NoModelOpenError()
