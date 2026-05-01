from fastapi import APIRouter, Request

from bridge.contracts.model import (
    FrameListResponse,
    JointListResponse,
    LoadCaseListResponse,
    LoadCombinationListResponse,
    LoadPatternListResponse,
    MaterialListResponse,
    SectionListResponse,
    UnitsResponse,
)
from bridge.services.model_reader import ModelReader
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000/model")


@router.get("/units", response_model=UnitsResponse)
def units(request: Request) -> UnitsResponse:
    reader = ModelReader(session_manager.adapter)
    units_info = reader.get_units()
    status = session_manager.adapter.status()
    return UnitsResponse(
        model_path=status.model_path or "",
        model_name=status.model_name or "",
        version_label=status.version_label or "",
        version_number=status.version_number or "",
        adapter_mode=status.adapter_mode,
        units=units_info,
        correlation_id=request.state.correlation_id,
    )


@router.get("/joints", response_model=JointListResponse)
def joints(
    request: Request,
    csys: str = "Global",
    include_restraints: bool = False,
) -> JointListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_joints(csys=csys, include_restraints=include_restraints)
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/frames", response_model=FrameListResponse)
def frames(request: Request, csys: str = "Global") -> FrameListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_frames(csys=csys)
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/materials", response_model=MaterialListResponse)
def materials(request: Request) -> MaterialListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_materials()
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/sections", response_model=SectionListResponse)
def sections(request: Request) -> SectionListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_sections()
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/load-patterns", response_model=LoadPatternListResponse)
def load_patterns(request: Request) -> LoadPatternListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_load_patterns()
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/load-cases", response_model=LoadCaseListResponse)
def load_cases(request: Request) -> LoadCaseListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_load_cases()
    response.correlation_id = request.state.correlation_id
    return response


@router.get("/load-combinations", response_model=LoadCombinationListResponse)
def load_combinations(request: Request) -> LoadCombinationListResponse:
    reader = ModelReader(session_manager.adapter)
    response = reader.list_load_combinations()
    response.correlation_id = request.state.correlation_id
    return response
