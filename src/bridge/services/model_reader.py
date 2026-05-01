from bridge.adapters.base import SapAdapter
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import (
    FrameListResponse,
    JointListResponse,
    LoadCaseListResponse,
    LoadCombinationListResponse,
    LoadPatternListResponse,
    MaterialListResponse,
    SectionListResponse,
)


class ModelReader:
    def __init__(self, adapter: SapAdapter) -> None:
        self._adapter = adapter

    def get_units(self) -> UnitsInfo:
        return self._adapter.get_units()

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        return self._adapter.list_joints(csys=csys, include_restraints=include_restraints)

    def list_frames(self, csys: str = "Global") -> FrameListResponse:
        return self._adapter.list_frames(csys=csys)

    def list_materials(self) -> MaterialListResponse:
        return self._adapter.list_materials()

    def list_sections(self) -> SectionListResponse:
        return self._adapter.list_sections()

    def list_load_patterns(self) -> LoadPatternListResponse:
        return self._adapter.list_load_patterns()

    def list_load_cases(self) -> LoadCaseListResponse:
        return self._adapter.list_load_cases()

    def list_load_combinations(self) -> LoadCombinationListResponse:
        return self._adapter.list_load_combinations()
