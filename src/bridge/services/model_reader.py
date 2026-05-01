from bridge.adapters.base import SapAdapter
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import JointListResponse


class ModelReader:
    def __init__(self, adapter: SapAdapter) -> None:
        self._adapter = adapter

    def get_units(self) -> UnitsInfo:
        return self._adapter.get_units()

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        return self._adapter.list_joints(csys=csys, include_restraints=include_restraints)
