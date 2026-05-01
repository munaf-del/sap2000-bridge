import importlib

import pytest
from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.config import Settings
from bridge.errors import BridgeError
import bridge.adapters.comtypes_adapter as comtypes_adapter
import bridge.services.session_manager as session_manager_module
from bridge.services.session_manager import SessionManager, session_manager


def test_app_imports_without_requiring_comtypes() -> None:
    module = importlib.import_module("bridge.api.main")

    assert module.app is app


def test_comtypes_adapter_import_does_not_crash() -> None:
    module = importlib.import_module("bridge.adapters.comtypes_adapter")

    assert hasattr(module, "ComtypesSapAdapter")
    assert hasattr(module, "check_ret")


def test_fake_adapter_remains_default() -> None:
    manager = SessionManager()

    assert manager.adapter.adapter_mode == "fake"


def test_comtypes_mode_without_comtypes_returns_adapter_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", None)
    monkeypatch.setattr(
        session_manager_module,
        "get_settings",
        lambda: Settings(adapter_mode="comtypes"),
    )
    session_manager.reset()

    try:
        client = TestClient(app)
        response = client.post("/sap2000/connect", json={"attach_to_running": True})
        body = response.json()

        assert response.status_code == 503
        assert body["error"]["http_status"] == 503
        assert body["error"]["bridge_code"] == "ADAPTER_UNAVAILABLE"
        assert body["error"]["correlation_id"]
    finally:
        monkeypatch.setattr(
            session_manager_module,
            "get_settings",
            lambda: Settings(adapter_mode="fake"),
        )
        session_manager.reset()


def test_check_ret_allows_success_and_rejects_failure() -> None:
    comtypes_adapter.check_ret(0, operation="GetVersion")
    comtypes_adapter.check_ret(None, operation="OptionalNoRet")

    with pytest.raises(BridgeError) as exc_info:
        comtypes_adapter.check_ret(7, operation="GetVersion", sap_context="cSapModel.GetVersion")

    assert getattr(exc_info.value, "bridge_code") == "SAP2000_RETURN_CODE"
    assert getattr(exc_info.value, "sap_ret") == 7
    assert getattr(exc_info.value, "sap_context") == "cSapModel.GetVersion"


def test_comtypes_placeholder_mentions_required_verification(monkeypatch) -> None:
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", object())
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings())

    with pytest.raises(BridgeError) as exc_info:
        adapter.create_helper()

    message = getattr(exc_info.value, "message")
    assert "VERIFY AGAINST INSTALLED SAP2000 API CHM" in message
    assert "VERIFY AGAINST SAP2000v1.tlb" in message
    assert "VERIFY comtypes tuple/byref behaviour on target machine" in message
