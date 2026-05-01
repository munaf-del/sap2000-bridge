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
    def __init__(
        self,
        version_result=None,
        point_obj=None,
        frame_obj=None,
        prop_material=None,
        prop_frame=None,
        load_patterns=None,
        load_cases=None,
        resp_combo=None,
    ) -> None:
        self.version_result = version_result if version_result is not None else ("SAP2000 v27", "27.0.0", 0)
        self.PointObj = point_obj or MockPointObj()
        self.FrameObj = frame_obj or MockFrameObj()
        self.PropMaterial = prop_material or MockPropMaterial()
        self.PropFrame = prop_frame or MockPropFrame()
        self.LoadPatterns = load_patterns or MockLoadPatterns()
        self.LoadCases = load_cases or MockLoadCases()
        self.RespCombo = resp_combo or MockRespCombo()

    def GetVersion(self):
        return self.version_result

    def GetPresentUnits(self):
        return 6

    def GetDatabaseUnits(self):
        return 6


class MockPointObj:
    def __init__(self, name_list_result=None, coord_results=None, all_points_result=None, all_points_error=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.coord_results = coord_results or {}
        self.all_points_result = all_points_result
        self.all_points_error = all_points_error or AttributeError("GetAllPoints")
        self.coord_names: list[str] = []

    def GetNameList(self, *args):
        return self.name_list_result

    def GetAllPoints(self, *args):
        if self.all_points_result is None:
            raise self.all_points_error
        return self.all_points_result

    def GetCoordCartesian(self, name, *args):
        self.coord_names.append(name)
        if name not in self.coord_results:
            raise RuntimeError(f"unknown point {name}")
        return self.coord_results[name]


class MockFrameObj:
    def __init__(self, name_list_result=None, points=None, sections=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.points = points or {}
        self.sections = sections or {}

    def GetNameList(self, *args):
        return self.name_list_result

    def GetPoints(self, name, *args):
        if name not in self.points:
            raise RuntimeError("frame points unavailable")
        start, end = self.points[name]
        return [start, end, 0]

    def GetSection(self, name, *args):
        if name not in self.sections:
            raise RuntimeError("frame section unavailable")
        return [self.sections[name], "", 0]


class MockPropMaterial:
    def __init__(self, name_list_result=None, material_types=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.material_types = material_types or {}

    def GetNameList(self, *args):
        return self.name_list_result

    def GetMaterial(self, name, *args):
        if name not in self.material_types:
            raise RuntimeError("material type unavailable")
        return [self.material_types[name], 0]


class MockPropFrame:
    def __init__(self, name_list_result=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]

    def GetNameList(self, *args):
        return self.name_list_result


class MockLoadPatterns:
    def __init__(self, name_list_result=None, load_types=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.load_types = load_types or {}

    def GetNameList(self, *args):
        return self.name_list_result

    def GetLoadType(self, name, *args):
        if name not in self.load_types:
            raise RuntimeError("load pattern type unavailable")
        return [self.load_types[name], 0]


class MockLoadCases:
    def __init__(self, name_list_result=None, case_types=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.case_types = case_types or {}

    def GetNameList(self, *args):
        return self.name_list_result

    def GetTypeOAPI(self, name, *args):
        if name not in self.case_types:
            raise RuntimeError("load case type unavailable")
        return [self.case_types[name], 0]


class MockRespCombo:
    def __init__(self, name_list_result=None, case_lists=None) -> None:
        self.name_list_result = name_list_result if name_list_result is not None else [0, (), 0]
        self.case_lists = case_lists or {}

    def GetNameList(self, *args):
        return self.name_list_result

    def GetCaseList(self, name, *args):
        if name not in self.case_lists:
            raise RuntimeError("combo case list unavailable")
        return self.case_lists[name]


class MockSapObject:
    def __init__(self, sap_model: MockSapModel | None = None) -> None:
        self.SapModel = sap_model or MockSapModel()
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
        adapter.run_analysis()

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


def configured_comtypes_adapter(monkeypatch, sap_model: MockSapModel | None = None):
    sap_object = MockSapObject(sap_model=sap_model)
    helper = MockHelper(sap_object=sap_object)
    client = MockComtypesClient(helper=helper)
    monkeypatch.setattr(comtypes_adapter.sys, "platform", "win32")
    monkeypatch.setattr(comtypes_adapter, "comtypes_client", client)
    monkeypatch.setattr(comtypes_adapter, "comtypes_module", MockComtypesModule())
    adapter = comtypes_adapter.ComtypesSapAdapter(settings=Settings(adapter_mode="comtypes", enable_real_com=True))
    adapter._sap_object = sap_object
    adapter._sap_model = sap_object.SapModel
    adapter._connected = True
    adapter._model_path = "C:/models/demo.sdb"
    adapter._version_label = "27.1.0"
    adapter._version_number = 27.1
    return adapter, sap_object


def test_get_version_normalizes_list_with_ret_code_last(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(version_result=["27.1.0", 27.1, 0]))

    response = adapter.get_version()

    assert response.version_label == "27.1.0"
    assert response.version_number == 27.1


def test_status_after_comtypes_connect_returns_normalized_version_number(monkeypatch) -> None:
    sap_model = MockSapModel(version_result=["27.1.0", 27.1, 0])
    sap_object = MockSapObject(sap_model=sap_model)
    helper = MockHelper(sap_object=sap_object)
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
        api_client = TestClient(app)
        connect_response = api_client.post("/sap2000/connect", json={"attach_to_running": True})
        status_response = api_client.get("/sap2000/status")

        assert connect_response.status_code == 200
        assert status_response.status_code == 200
        assert status_response.json()["version_label"] == "27.1.0"
        assert status_response.json()["version_number"] == 27.1
    finally:
        monkeypatch.setattr(
            session_manager_module,
            "get_settings",
            lambda: Settings(adapter_mode="fake", enable_real_com=False),
        )
        session_manager.reset()


def test_get_version_normalizes_tuple_with_ret_code_first(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(version_result=(0, "27.1.0", 27.1)))

    response = adapter.get_version()

    assert response.version_label == "27.1.0"
    assert response.version_number == 27.1


def test_units_enum_six_maps_verified_components(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    units = adapter.get_units()

    assert units.present_raw == 6
    assert units.database_raw == 6
    assert units.present == "kN_m_C"
    assert units.database == "kN_m_C"
    assert units.length == "m"
    assert units.force == "kN"
    assert units.moment == "kN-m"
    assert units.temperature == "C"


def test_get_name_list_parsing_with_ret_code_last(monkeypatch) -> None:
    point_obj = MockPointObj(name_list_result=[2, ("0", "1"), 0])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    assert adapter._get_point_names() == ["0", "1"]


def test_get_name_list_parsing_with_ret_code_first(monkeypatch) -> None:
    point_obj = MockPointObj(name_list_result=[0, 2, ("0", "1")])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    assert adapter._get_point_names() == ["0", "1"]


def test_get_name_list_zero_points_returns_empty_list(monkeypatch) -> None:
    point_obj = MockPointObj(name_list_result=[0, (), 0])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    assert adapter._get_point_names() == []


def test_get_coord_cartesian_parsing_with_ret_code_last(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    assert adapter._parse_get_coord_cartesian_result([1.0, 2.0, 3.0, 0], "P1") == (1.0, 2.0, 3.0)


def test_get_coord_cartesian_parsing_with_ret_code_first(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    assert adapter._parse_get_coord_cartesian_result([0, 1.0, 2.0, 3.0], "P1") == (1.0, 2.0, 3.0)


def test_point_name_int_zero_is_converted_to_string_before_coord_call(monkeypatch) -> None:
    point_obj = MockPointObj(
        name_list_result=[1, (0,), 0],
        coord_results={"0": [1.0, 2.0, 3.0, 0]},
    )
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    response = adapter.list_joints()

    assert response.joints[0].name == "0"
    assert point_obj.coord_names == ["0"]


def test_empty_model_returns_empty_joints_without_coord_calls(monkeypatch) -> None:
    point_obj = MockPointObj(name_list_result=[0, (), 0])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    response = adapter.list_joints()

    assert response.joints == []
    assert point_obj.coord_names == []


def test_get_all_points_zero_count_returns_empty_joints(monkeypatch) -> None:
    point_obj = MockPointObj(all_points_result=[0, (), (), (), (), 0])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    response = adapter.list_joints()

    assert response.joints == []
    assert point_obj.coord_names == []


def test_get_all_points_valid_arrays_returns_joints(monkeypatch) -> None:
    point_obj = MockPointObj(all_points_result=[2, ("P1", "P2"), (0.0, 1.0), (2.0, 3.0), (4.0, 5.0), 0])
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(point_obj=point_obj))

    response = adapter.list_joints()

    assert [joint.name for joint in response.joints] == ["P1", "P2"]
    assert response.joints[1].x == 1.0
    assert response.joints[1].y == 3.0
    assert response.joints[1].z == 5.0
    assert point_obj.coord_names == []


def test_malformed_coordinate_tuple_returns_standard_error_envelope(monkeypatch) -> None:
    point_obj = MockPointObj(name_list_result=[1, ("P1",), 0], coord_results={"P1": [1.0, 2.0, 0]})
    sap_model = MockSapModel(point_obj=point_obj)
    sap_object = MockSapObject(sap_model=sap_model)
    helper = MockHelper(sap_object=sap_object)
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
    session_manager.adapter._sap_object = sap_object
    session_manager.adapter._sap_model = sap_model
    session_manager.adapter._connected = True
    session_manager.adapter._model_path = "C:/models/demo.sdb"
    session_manager.adapter._version_label = "27.1.0"
    session_manager.adapter._version_number = 27.1

    try:
        response = TestClient(app).get("/sap2000/model/joints")
        body = response.json()

        assert response.status_code == 501
        assert body["error"]["bridge_code"] == "SAP2000_COM_SIGNATURE_UNVERIFIED"
        assert body["error"]["correlation_id"]
    finally:
        monkeypatch.setattr(
            session_manager_module,
            "get_settings",
            lambda: Settings(adapter_mode="fake", enable_real_com=False),
        )
        session_manager.reset()


def test_missing_sdb_path_returns_model_file_not_found(monkeypatch, tmp_path) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    with pytest.raises(BridgeError) as exc_info:
        adapter._prepare_model_path(str(tmp_path / "missing.sdb"), copy_to_workspace=False)

    assert exc_info.value.bridge_code == "MODEL_FILE_NOT_FOUND"


def test_non_sdb_path_returns_invalid_model_file(monkeypatch, tmp_path) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)
    file_path = tmp_path / "model.txt"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(BridgeError) as exc_info:
        adapter._prepare_model_path(str(file_path), copy_to_workspace=False)

    assert exc_info.value.bridge_code == "INVALID_MODEL_FILE"


def test_copy_permission_error_returns_model_file_locked(monkeypatch, tmp_path) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)
    source_path = tmp_path / "model.sdb"
    source_path.write_text("", encoding="utf-8")
    workspace = tmp_path / "workspace"
    adapter._settings.sap2000_workspace = str(workspace)

    def raise_permission_error(*args, **kwargs):
        raise PermissionError("locked")

    monkeypatch.setattr(comtypes_adapter.shutil, "copy2", raise_permission_error)

    with pytest.raises(BridgeError) as exc_info:
        adapter._prepare_model_path(str(source_path), copy_to_workspace=True)

    assert exc_info.value.bridge_code == "MODEL_FILE_LOCKED"


def test_copy_to_same_workspace_file_does_not_copy(monkeypatch, tmp_path) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)
    source_path = tmp_path / "model.sdb"
    source_path.write_text("", encoding="utf-8")
    adapter._settings.sap2000_workspace = str(tmp_path)
    copy_calls = []
    monkeypatch.setattr(comtypes_adapter.shutil, "copy2", lambda *args, **kwargs: copy_calls.append(args))

    prepared_path = adapter._prepare_model_path(str(source_path), copy_to_workspace=True)

    assert prepared_path == source_path
    assert copy_calls == []


def test_comtypes_metadata_name_parser_supports_ret_code_last(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    assert adapter._parse_name_list_result([2, ("A", "B"), 0], "FrameObj.GetNameList") == ["A", "B"]


def test_comtypes_metadata_name_parser_supports_ret_code_first(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    assert adapter._parse_name_list_result([0, 2, ("A", "B")], "FrameObj.GetNameList") == ["A", "B"]


def test_comtypes_empty_metadata_lists_return_empty_responses(monkeypatch) -> None:
    adapter, _ = configured_comtypes_adapter(monkeypatch)

    assert adapter.list_frames().frames == []
    assert adapter.list_materials().materials == []
    assert adapter.list_sections().sections == []
    assert adapter.list_load_patterns().load_patterns == []
    assert adapter.list_load_cases().load_cases == []
    assert adapter.list_load_combinations().load_combinations == []


def test_comtypes_frame_metadata_parses_names_points_and_sections(monkeypatch) -> None:
    frame_obj = MockFrameObj(
        name_list_result=[1, ("F1",), 0],
        points={"F1": ("1", "2")},
        sections={"F1": "Default"},
    )
    adapter, _ = configured_comtypes_adapter(monkeypatch, MockSapModel(frame_obj=frame_obj))

    response = adapter.list_frames()

    assert len(response.frames) == 1
    assert response.frames[0].name == "F1"
    assert response.frames[0].start_joint == "1"
    assert response.frames[0].end_joint == "2"
    assert response.frames[0].section == "Default"
    assert response.model_path == "C:/models/demo.sdb"
    assert response.adapter_mode == "comtypes"
    assert response.units.present == "kN_m_C"


def test_comtypes_material_section_load_metadata_shapes(monkeypatch) -> None:
    sap_model = MockSapModel(
        prop_material=MockPropMaterial(name_list_result=[2, ("CONC", "STEEL"), 0], material_types={"CONC": 2}),
        prop_frame=MockPropFrame(name_list_result=[1, ("R1",), 0]),
        load_patterns=MockLoadPatterns(name_list_result=[1, ("DEAD",), 0], load_types={"DEAD": 1}),
        load_cases=MockLoadCases(name_list_result=[1, ("DEAD",), 0], case_types={"DEAD": 1}),
        resp_combo=MockRespCombo(name_list_result=[1, ("ULS",), 0], case_lists={"ULS": [2, ("DEAD", "LIVE"), (1.2, 1.5), 0]}),
    )
    adapter, _ = configured_comtypes_adapter(monkeypatch, sap_model)

    materials = adapter.list_materials().materials
    sections = adapter.list_sections().sections
    load_patterns = adapter.list_load_patterns().load_patterns
    load_cases = adapter.list_load_cases().load_cases
    combos = adapter.list_load_combinations().load_combinations

    assert materials[0].name == "CONC"
    assert materials[0].material_type == 2
    assert materials[1].name == "STEEL"
    assert materials[1].material_type is None
    assert sections == [comtypes_adapter.FrameSection(name="R1")]
    assert load_patterns[0].name == "DEAD"
    assert load_patterns[0].load_type == 1
    assert load_patterns[0].self_weight_multiplier is None
    assert load_cases[0].name == "DEAD"
    assert load_cases[0].case_type == 1
    assert combos[0].name == "ULS"
    assert [(item.name, item.scale_factor) for item in combos[0].items] == [("DEAD", 1.2), ("LIVE", 1.5)]


def test_malformed_comtypes_metadata_tuple_returns_standard_error_envelope(monkeypatch) -> None:
    sap_model = MockSapModel(frame_obj=MockFrameObj(name_list_result=[1, 0]))
    sap_object = MockSapObject(sap_model=sap_model)
    helper = MockHelper(sap_object=sap_object)
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
    session_manager.adapter._sap_object = sap_object
    session_manager.adapter._sap_model = sap_model
    session_manager.adapter._connected = True
    session_manager.adapter._model_path = "C:/models/demo.sdb"
    session_manager.adapter._version_label = "27.1.0"
    session_manager.adapter._version_number = 27.1

    try:
        response = TestClient(app).get("/sap2000/model/frames")
        body = response.json()

        assert response.status_code == 502
        assert body["error"]["bridge_code"] == "SAP2000_COM_ERROR"
        assert body["error"]["sap_context"] == "FrameObj.GetNameList"
        assert body["error"]["correlation_id"]
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
        "manual_real_frames.py",
        "manual_real_materials.py",
        "manual_real_sections.py",
        "manual_real_load_patterns.py",
        "manual_real_load_cases.py",
        "manual_real_load_combinations.py",
        "manual_real_attach_diagnostics.py",
        "manual_real_point_diagnostics.py",
        "manual_real_metadata_diagnostics.py",
    ]

    for script_name in scripts:
        script_path = Path(__file__).resolve().parents[1] / "examples" / script_name
        spec = importlib.util.spec_from_file_location(script_name.removesuffix(".py"), script_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "main")
