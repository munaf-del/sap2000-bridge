from bridge.adapters.base import SapAdapter
from bridge.adapters.fake_adapter import FakeSapAdapter
from bridge.config import get_settings
from bridge.contracts.model import OpenModelResponse, SapSessionInfo, SapStatusResponse
from bridge.contracts.requests import ConnectRequest, LaunchRequest, OpenModelRequest


class SessionManager:
    def __init__(self) -> None:
        self.adapter: SapAdapter
        self._last_status: SapStatusResponse | None = None
        self.last_correlation_id: str | None = None
        self._configure_adapter()

    def _configure_adapter(self) -> None:
        settings = get_settings()
        if settings.adapter_mode == "fake":
            self.adapter: SapAdapter = FakeSapAdapter()
        else:
            from bridge.adapters.comtypes_adapter import ComtypesSapAdapter

            self.adapter = ComtypesSapAdapter()
        self._last_status = None
        self.last_correlation_id = None

    def reset(self) -> None:
        self._configure_adapter()

    def status(self, correlation_id: str) -> SapStatusResponse:
        response = self.adapter.status()
        return self._record_status(response=response, correlation_id=correlation_id)

    def connect(self, payload: ConnectRequest, correlation_id: str) -> SapSessionInfo:
        if self._is_connected():
            return self._session_info_from_status(correlation_id=correlation_id)

        response = self.adapter.connect(attach_to_running=payload.attach_to_running)
        response.correlation_id = correlation_id
        self._record_status(response=self.adapter.status(), correlation_id=correlation_id)
        return response

    def launch(self, payload: LaunchRequest, correlation_id: str) -> SapSessionInfo:
        if self._is_connected():
            return self._session_info_from_status(correlation_id=correlation_id)

        response = self.adapter.launch(
            exe_path=payload.exe_path,
            visible=payload.visible,
            startup_delay_s=payload.startup_delay_s,
        )
        response.correlation_id = correlation_id
        self._record_status(response=self.adapter.status(), correlation_id=correlation_id)
        return response

    def open_model(self, payload: OpenModelRequest, correlation_id: str) -> OpenModelResponse:
        response = self.adapter.open_model(
            path=payload.path,
            copy_to_workspace=payload.copy_to_workspace,
        )
        response.correlation_id = correlation_id
        self._record_status(response=self.adapter.status(), correlation_id=correlation_id)
        return response

    def _is_connected(self) -> bool:
        return self.adapter.status().connected

    def _record_status(self, response: SapStatusResponse, correlation_id: str) -> SapStatusResponse:
        response.correlation_id = correlation_id
        self._last_status = response
        self.last_correlation_id = correlation_id
        return response

    def _session_info_from_status(self, correlation_id: str) -> SapSessionInfo:
        status = self._record_status(response=self.adapter.status(), correlation_id=correlation_id)
        return SapSessionInfo(
            connected=status.connected,
            launched_by_bridge=status.launched_by_bridge,
            version_label=status.version_label or "",
            version_number=status.version_number or "",
            adapter_mode=status.adapter_mode,
            correlation_id=correlation_id,
        )


session_manager = SessionManager()
