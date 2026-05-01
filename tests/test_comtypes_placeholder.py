import importlib
import importlib.util
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.config import Settings
from bridge.errors import BridgeError
import bridge.adapters.comtypes_adapter as comtypes_adapter
import bridge.services.session_manager as session_manager_module
from bridge.services.session_manager import SessionManager, session_manager


class MockSapModel:
    def GetVersion(self):
        return ("SAP2000 v27", "27.0.0", 0)


class MockSapObject:
    def __init__(self) -> None:
        self.SapModel = MockSapModel()
        self.application_start_calls = 0

    def ApplicationStart(self):
        self.application_start_calls += 1
        return 0


class MockHelper:
    def __init__(self, sap_object: MockSapObject, attach_fails: bool = False) -> None:
        self.sap_object = sap_object
        self.attach_fails = attach_fails
        self.get_object_calls: list[str] = []
        self.create_object_calls: list[str] = []

    def GetObject(self, progid: str):
        self.get_object_calls.append(progid)
        if self.attach_fails:
            raise RuntimeError("SAP2000 is not running")
        return self.sap_object

    def CreateObject(self, exe_path: str):
        self.create_object_calls.append(exe_path)
        return self.sap_object


class MockComtypesClient:
    def __init__(self, helper: MockHelper) -> None:
        self.helper = helper
        self.created_helper_progids: list[str] = []

    def CreateObject(self, progid: str):
        self.created_helper_progids.append(progid)
        return self.helper


class MockComtypesModule:
    def __init__(self) -> None:
        self.coinitialize_calls = 0
        self.couninitialize_calls = 0

    def CoInitialize(self) -> None:
        self.coinitialize_calls += 1

    def CoUninitialize(self) -> None:
        self.couninitialize_calls += 1


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


def test_tests_force_fake_adapter_even_if_outer_shell_requested_comtypes() -> None:
    from bridge.config import get_settings

    get_settings.cache_clear()
    session_manager.reset()

    try:
        assert get_settings().adapter_mode == "fake"
        assert get_settings().enable_real_com is False
        assert session_manager.adapter.adapter_mode == "fake"
    finally:
        get_settings.cache_clear()


def test_comtypes_mode_without_comtypes_returns_adapter_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", None)
    monkeypatch.setattr(
        session_manager_module,
        "get_settings",
        lambda: Settings(adapter_mode="comtypes", enable_real_com=True),
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


def test_comtypes_mode_without_enable_flag_returns_real_com_disabled(monkeypatch) -> None:
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", object())
    monkeypatch.setattr(
        session_manager_module,
        "get_settings",
        lambda: Settings(adapter_mode="comtypes", enable_real_com=False),
    )
    session_manager.reset()

    try:
        client = TestClient(app)
        response = client.post("/sap2000/connect", json={"attach_to_running": True})
        body = response.json()

        assert response.status_code == 503
        assert body["error"]["http_status"] == 503
        assert body["error"]["bridge_code"] == "REAL_COM_DISABLED"
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
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", object())
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings(enable_real_com=True))

    with pytest.raises(BridgeError) as exc_info:
        adapter.list_frames()

    message = getattr(exc_info.value, "message")
    assert "VERIFY AGAINST INSTALLED SAP2000 API CHM" in message
    assert "VERIFY AGAINST SAP2000v1.tlb" in message
    assert "VERIFY comtypes tuple/byref behaviour on target machine" in message


def test_connect_attach_only_does_not_call_launch_create_or_start(monkeypatch) -> None:
    sap_object = MockSapObject()
    helper = MockHelper(sap_object=sap_object)
    client = MockComtypesClient(helper=helper)
    com_module = MockComtypesModule()
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", client)
    monkeypatch.setattr(comtypes_adapter, "comtypes_module", com_module)
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings(adapter_mode="comtypes", enable_real_com=True))

    response = adapter.connect(attach_to_running=True)

    assert response.connected is True
    assert response.launched_by_bridge is False
    assert response.version_number == "27.0.0"
    assert client.created_helper_progids == ["SAP2000v1.Helper"]
    assert helper.get_object_calls == ["CSI.SAP2000.API.SapObject"]
    assert helper.create_object_calls == []
    assert sap_object.application_start_calls == 0
    assert adapter.helper_progid_used == "SAP2000v1.Helper"
    assert com_module.coinitialize_calls >= 1


def test_launch_path_is_separate_from_attach_path(monkeypatch, tmp_path) -> None:
    sap_object = MockSapObject()
    helper = MockHelper(sap_object=sap_object)
    client = MockComtypesClient(helper=helper)
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", client)
    monkeypatch.setattr(comtypes_adapter, "comtypes_module", MockComtypesModule())
    exe_path = tmp_path / "SAP2000.exe"
    exe_path.write_text("", encoding="utf-8")
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings(adapter_mode="comtypes", enable_real_com=True))

    response = adapter.launch(exe_path=str(exe_path), startup_delay_s=0)

    assert response.connected is True
    assert response.launched_by_bridge is True
    assert helper.get_object_calls == []
    assert helper.create_object_calls == [str(exe_path)]
    assert sap_object.application_start_calls == 1


def test_helper_creation_falls_back_to_csi_helper_progid(monkeypatch) -> None:
    sap_object = MockSapObject()
    helper = MockHelper(sap_object=sap_object)

    def create_object(progid: str):
        if progid == "SAP2000v1.Helper":
            raise RuntimeError("primary helper unavailable")
        return helper

    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", SimpleNamespace(CreateObject=create_object))
    monkeypatch.setattr(comtypes_adapter, "comtypes_module", MockComtypesModule())
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings(adapter_mode="comtypes", enable_real_com=True))

    adapter.connect(attach_to_running=True)

    assert adapter.helper_progid_used == "CSiAPIv1.Helper"
    assert helper.get_object_calls == ["CSI.SAP2000.API.SapObject"]


def test_attach_failure_returns_standard_error_envelope(monkeypatch) -> None:
    sap_object = MockSapObject()
    helper = MockHelper(sap_object=sap_object, attach_fails=True)
    client = MockComtypesClient(helper=helper)
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", client)
    monkeypatch.setattr(comtypes_adapter, "comtypes_module", MockComtypesModule())
    monkeypatch.setattr(
        session_manager_module,
        "get_settings",
        lambda: Settings(adapter_mode="comtypes", enable_real_com=True),
    )
    session_manager.reset()

    try:
        response = TestClient(app).post("/sap2000/connect", json={"attach_to_running": True})
        body = response.json()

        assert response.status_code == 503
        assert body["error"]["bridge_code"] == "SAP2000_NOT_RUNNING"
        assert body["error"]["message"] == "Could not attach to a running SAP2000 instance."
        assert body["error"]["sap_context"] == "Helper.GetObject"
        assert body["error"]["retryable"] is True
        assert body["error"]["correlation_id"]
        assert helper.create_object_calls == []
        assert sap_object.application_start_calls == 0
    finally:
        monkeypatch.setattr(
            session_manager_module,
            "get_settings",
            lambda: Settings(adapter_mode="fake", enable_real_com=False),
        )
        session_manager.reset()


def test_manual_real_com_scripts_import_without_executing_com(monkeypatch) -> None:
    monkeypatch.delenv("SAP2000_BRIDGE_ENABLE_REAL_COM", raising=False)
    scripts = [
        "manual_real_connect.py",
        "manual_real_launch.py",
        "manual_real_open_model.py",
        "manual_real_units.py",
        "manual_real_joints.py",
        "manual_real_attach_diagnostics.py",
    ]

    for script_name in scripts:
        script_path = Path(__file__).resolve().parents[1] / "examples" / script_name
        spec = importlib.util.spec_from_file_location(script_name.removesuffix(".py"), script_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "main")
