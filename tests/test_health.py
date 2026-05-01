from fastapi.testclient import TestClient

from bridge.api.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "sap2000-local-bridge",
        "version": "0.1.0",
    }


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
    assert isinstance(body["sap2000_target"]["com_registration_ready"], bool)
    assert body["correlation_id"]
