from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


def fresh_client() -> TestClient:
    session_manager.adapter.__init__()
    return TestClient(app)


def test_status_initial_state() -> None:
    client = fresh_client()
    response = client.get("/sap2000/status")
    body = response.json()

    assert response.status_code == 200
    assert body["connected"] is False
    assert body["model_open"] is False
    assert body["adapter_mode"] == "fake"
    assert body["correlation_id"]


def test_connect() -> None:
    client = fresh_client()
    response = client.post("/sap2000/connect", json={"attach_to_running": True})
    body = response.json()

    assert response.status_code == 200
    assert body["connected"] is True
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["adapter_mode"] == "fake"
    assert body["correlation_id"]


def test_launch() -> None:
    client = fresh_client()
    response = client.post(
        "/sap2000/launch",
        json={"exe_path": None, "visible": True, "startup_delay_s": 3.0},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["connected"] is True
    assert body["version_number"] == "0.1.0-fake"
    assert body["correlation_id"]


def test_open_model() -> None:
    client = fresh_client()
    client.post("/sap2000/connect", json={"attach_to_running": True})
    response = client.post(
        "/sap2000/open-model",
        json={"path": "C:/models/demo.sdb", "copy_to_workspace": False},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["model_open"] is True
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["units"]["present"] == "kN_m_C"
    assert body["correlation_id"]


def test_not_connected_error_shape() -> None:
    client = fresh_client()
    response = client.post(
        "/sap2000/open-model",
        json={"path": "C:/models/demo.sdb", "copy_to_workspace": False},
    )
    body = response.json()

    assert response.status_code == 409
    assert set(body.keys()) == {"error"}
    assert body["error"]["http_status"] == 409
    assert body["error"]["bridge_code"] == "NOT_CONNECTED"
    assert body["error"]["sap_ret"] is None
    assert body["error"]["sap_context"] is None
    assert body["error"]["correlation_id"]
