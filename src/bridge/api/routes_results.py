from fastapi import APIRouter, Query, Request

from bridge.contracts.results import FrameForceSetResponse, JointReactionSet, ModalPeriodSetResponse
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


@router.get("/frame-forces", response_model=FrameForceSetResponse)
def frame_forces(
    request: Request,
    frame_name: str | None = None,
    case_name: str | None = None,
    combo_name: str | None = None,
    case_names: list[str] = Query(default_factory=list),
    combo_names: list[str] = Query(default_factory=list),
) -> FrameForceSetResponse:
    cases = [case_name] if case_name else []
    combos = [combo_name] if combo_name else []
    cases.extend(case_names)
    combos.extend(combo_names)
    reader = ResultsReader(session_manager.adapter)
    response = reader.frame_forces(frame_name=frame_name, case_names=cases, combo_names=combos)
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/modal-periods", response_model=ModalPeriodSetResponse)
def modal_periods(
    request: Request,
    case_name: str | None = None,
    case_names: list[str] = Query(default_factory=list),
) -> ModalPeriodSetResponse:
    cases = [case_name] if case_name else []
    cases.extend(case_names)
    reader = ResultsReader(session_manager.adapter)
    response = reader.modal_periods(case_names=cases)
    response.correlation_id = request.state.correlation_id
    return response
