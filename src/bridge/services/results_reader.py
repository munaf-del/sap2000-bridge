from bridge.adapters.base import SapAdapter
from bridge.contracts.results import FrameForceSetResponse, JointReactionSet, ModalPeriodSetResponse


class ResultsReader:
    def __init__(self, adapter: SapAdapter) -> None:
        self._adapter = adapter

    def joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        return self._adapter.extract_joint_reactions(
            point_name=point_name,
            case_names=case_names,
            combo_names=combo_names,
        )

    def frame_forces(
        self,
        frame_name: str | None,
        case_names: list[str],
        combo_names: list[str],
    ) -> FrameForceSetResponse:
        return self._adapter.extract_frame_forces(
            frame_name=frame_name,
            case_names=case_names,
            combo_names=combo_names,
        )

    def modal_periods(self, case_names: list[str]) -> ModalPeriodSetResponse:
        return self._adapter.extract_modal_periods(case_names=case_names)
