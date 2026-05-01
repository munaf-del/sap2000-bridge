from datetime import datetime, timezone
from uuid import uuid4

from bridge.adapters.base import SapAdapter
from bridge.contracts.results import AnalysisJobStatus
from bridge.errors import BridgeError


ACTIVE_ANALYSIS_STATES = {"queued", "running"}


class AnalysisRunner:
    def __init__(self) -> None:
        self._jobs: dict[str, AnalysisJobStatus] = {}
        self._active_job_id: str | None = None

    def reset(self) -> None:
        self._jobs.clear()
        self._active_job_id = None

    def submit(
        self,
        adapter: SapAdapter,
        correlation_id: str,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        if save_before_run:
            raise BridgeError(
                http_status=409,
                bridge_code="READ_ONLY_VIOLATION",
                message="save_before_run is disabled because the MVP must not save or modify SAP2000 models.",
                retryable=False,
            )
        if self._active_job_id and self._jobs[self._active_job_id].state in ACTIVE_ANALYSIS_STATES:
            raise BridgeError(
                http_status=409,
                bridge_code="ANALYSIS_ALREADY_RUNNING",
                message="An analysis job is already active. Wait for it to finish before submitting another job.",
                retryable=True,
            )

        selected_cases = case_names or []
        status = adapter.status()
        now = datetime.now(timezone.utc)
        job = AnalysisJobStatus(
            job_id=f"analysis-{uuid4()}",
            state="queued",
            model_path=status.model_path or "",
            model_name=status.model_name or "",
            version_label=status.version_label or "",
            version_number=status.version_number or "",
            adapter_mode=status.adapter_mode,
            submitted_at_utc=now,
            case_status={case_name: "queued" for case_name in (selected_cases or ["ALL"])},
            correlation_id=correlation_id,
        )
        self._jobs[job.job_id] = job
        self._active_job_id = job.job_id
        self._run_immediate_fake_lifecycle(adapter=adapter, job=job, case_names=selected_cases)
        job.correlation_id = correlation_id
        return job

    def get_status(self, job_id: str, correlation_id: str) -> AnalysisJobStatus:
        job = self._jobs.get(job_id)
        if job is None:
            raise BridgeError(
                http_status=404,
                bridge_code="UNKNOWN_ANALYSIS_JOB",
                message=f"Analysis job was not found: {job_id}",
                retryable=False,
            )
        job.correlation_id = correlation_id
        return job

    def _run_immediate_fake_lifecycle(
        self,
        adapter: SapAdapter,
        job: AnalysisJobStatus,
        case_names: list[str],
    ) -> None:
        job.state = "running"
        job.started_at_utc = datetime.now(timezone.utc)
        job.case_status = {case_name: "running" for case_name in (case_names or ["ALL"])}
        try:
            if "__FAIL__" in case_names:
                raise BridgeError(
                    http_status=500,
                    bridge_code="FAKE_ANALYSIS_FAILED",
                    message="Fake analysis failure requested by __FAIL__ case name.",
                    retryable=False,
                )
            adapter.run_analysis(save_before_run=False, case_names=case_names)
            job.state = "succeeded"
            job.case_status = {case_name: "succeeded" for case_name in (case_names or ["ALL"])}
        except BridgeError as exc:
            job.state = "failed"
            job.error_message = exc.message
            job.case_status = {case_name: "failed" for case_name in (case_names or ["ALL"])}
        finally:
            job.finished_at_utc = datetime.now(timezone.utc)
            if self._active_job_id == job.job_id:
                self._active_job_id = None


analysis_runner = AnalysisRunner()
