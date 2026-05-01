from fastapi import APIRouter, Request

from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import JointListResponse
from bridge.services.model_reader import ModelReader
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000/model")


@router.get("/units")
def units(request: Request) -> dict[str, UnitsInfo | str]:
    reader = ModelReader(session_manager.adapter)
    return {
        "units": reader.get_units(),
        "correlation_id": request.state.correlation_id,
    }


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
