from bridge.adapters.base import SapAdapter
from bridge.contracts.results import JointReactionSet


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
