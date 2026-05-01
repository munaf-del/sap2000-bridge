from fastapi import APIRouter, Query, Request

from bridge.contracts.results import JointReactionSet
from bridge.services.results_reader import ResultsReader
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000/results")


@router.get("/joint-reactions", response_model=JointReactionSet)
def joint_reactions(
    request: Request,
    point_name: str,
    case_name: str | None = None,
    combo_name: str | None = None,
    case_names: list[str] = Query(default_factory=list),
    combo_names: list[str] = Query(default_factory=list),
) -> JointReactionSet:
    cases = [case_name] if case_name else []
    combos = [combo_name] if combo_name else []
    cases.extend(case_names)
    combos.extend(combo_names)
    reader = ResultsReader(session_manager.adapter)
    response = reader.joint_reactions(
        point_name=point_name,
        case_names=cases,
        combo_names=combos,
    )
    response.correlation_id = request.state.correlation_id
    return response
