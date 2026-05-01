from fastapi import APIRouter, Request

from bridge.contracts.requests import AnalysisRequest
from bridge.contracts.results import AnalysisJobStatus
from bridge.services.analysis_runner import analysis_runner
from bridge.services.session_manager import session_manager

router = APIRouter(prefix="/sap2000")


@router.post("/analyze", response_model=AnalysisJobStatus)
def analyze(payload: AnalysisRequest, request: Request) -> AnalysisJobStatus:
    return analysis_runner.submit(
        adapter=session_manager.adapter,
        correlation_id=request.state.correlation_id,
        save_before_run=payload.save_before_run,
        case_names=payload.case_names,
    )


@router.post("/analyse", response_model=AnalysisJobStatus)
def analyse(payload: AnalysisRequest, request: Request) -> AnalysisJobStatus:
    return analyze(payload=payload, request=request)


@router.get("/analyze/status/{job_id}", response_model=AnalysisJobStatus)
def analyze_status(job_id: str, request: Request) -> AnalysisJobStatus:
    return analysis_runner.get_status(job_id=job_id, correlation_id=request.state.correlation_id)


@router.get("/analyse/status/{job_id}", response_model=AnalysisJobStatus)
def analyse_status(job_id: str, request: Request) -> AnalysisJobStatus:
    return analyze_status(job_id=job_id, request=request)
