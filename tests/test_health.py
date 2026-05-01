from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.config import Settings
import bridge.api.routes_health as routes_health


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["service"] == "sap2000-local-bridge"
    assert body["version"] == "0.1.0"
    assert body["correlation_id"]


def test_bridge_info_has_capabilities_and_correlation_id() -> None:
    client = TestClient(app)
    response = client.get("/bridge/info")
    body = response.json()

    assert response.status_code == 200
    assert body["bridge_version"] == "0.1.0"
    assert body["adapter_mode"] == "fake"
    assert body["read_only"] is True
    assert body["writeback_enabled"] is False
    assert "POST /sap2000/analyse" in body["supported_endpoints"]
    assert body["sap2000_target"]["configured_version"] == "SAP2000 27"
    assert body["sap2000_target"]["install_dir"].endswith("SAP2000 27")
    assert body["install_validation"]["configured_version"] == "SAP2000 27"
    assert isinstance(body["install_validation"]["com_registration_ready"], bool)
    assert isinstance(body["install_validation"]["warnings"], list)
    assert body["correlation_id"]


def test_bridge_info_handles_missing_sap2000_install(monkeypatch, tmp_path) -> None:
    missing_dir = tmp_path / "missing" / "SAP2000 99"

    monkeypatch.setattr(
        routes_health,
        "get_settings",
        lambda: Settings(
            csi_products_root=str(tmp_path / "missing"),
            sap2000_install_dir=str(missing_dir),
            sap2000_exe_path=str(missing_dir / "SAP2000.exe"),
            sap2000_api_dll_path=str(missing_dir / "SAP2000v1.dll"),
            csi_api_dll_path=str(missing_dir / "CSiAPIv1.dll"),
            sap2000_oapi_chm_path=str(missing_dir / "CSI_OAPI_Documentation.chm"),
        ),
    )

    client = TestClient(app)
    response = client.get("/bridge/info")
    body = response.json()

    assert response.status_code == 200
    assert body["sap2000_target"]["configured_version"] == "SAP2000 99"
    assert body["install_validation"]["all_required_present"] is False
    assert body["install_validation"]["sap2000_exe_present"] is False
    assert body["install_validation"]["warnings"]
    assert body["correlation_id"]
