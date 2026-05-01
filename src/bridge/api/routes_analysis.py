from fastapi import APIRouter, Request

from bridge.contracts.requests import AnalysisRequest
from bridge.contracts.results import AnalysisJobStatus
from bridge.services.analysis_runner import AnalysisRunner
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000")


@router.post("/analyze", response_model=AnalysisJobStatus)
def analyze(payload: AnalysisRequest, request: Request) -> AnalysisJobStatus:
    runner = AnalysisRunner(session_manager.adapter)
    response = runner.run(save_before_run=payload.save_before_run, case_names=payload.case_names)
    response.correlation_id = request.state.correlation_id
    return response


@router.post("/analyse", response_model=AnalysisJobStatus)
def analyse(payload: AnalysisRequest, request: Request) -> AnalysisJobStatus:
    return analyze(payload=payload, request=request)
