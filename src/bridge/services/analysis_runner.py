from bridge.adapters.base import SapAdapter
from bridge.contracts.results import AnalysisJobStatus
from bridge.errors import BridgeError


class AnalysisRunner:
    def __init__(self, adapter: SapAdapter) -> None:
        self._adapter = adapter

    def run(self, save_before_run: bool = False, case_names: list[str] | None = None) -> AnalysisJobStatus:
        if save_before_run:
            raise BridgeError(
                http_status=409,
                bridge_code="READ_ONLY_VIOLATION",
                message="save_before_run is disabled because the MVP must not save or modify SAP2000 models.",
                retryable=False,
            )
        return self._adapter.run_analysis(save_before_run=save_before_run, case_names=case_names or [])
