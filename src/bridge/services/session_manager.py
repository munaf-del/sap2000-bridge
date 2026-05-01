from bridge.adapters.base import SapAdapter
from bridge.adapters.fake_adapter import FakeSapAdapter
from bridge.config import get_settings


class SessionManager:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.adapter_mode == "fake":
            self.adapter: SapAdapter = FakeSapAdapter()
        else:
            from bridge.adapters.comtypes_adapter import ComtypesSapAdapter

            self.adapter = ComtypesSapAdapter()


session_manager = SessionManager()
