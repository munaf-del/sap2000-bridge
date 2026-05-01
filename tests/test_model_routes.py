from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


def prepared_client(open_model: bool = True) -> TestClient:
    session_manager.adapter.__init__()
    client = TestClient(app)
    client.post("/sap2000/connect", json={"attach_to_running": True})
    if open_model:
        client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})
    return client


def test_units() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/units")
    body = response.json()

    assert response.status_code == 200
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["version_number"] == "0.1.0-fake"
    assert body["adapter_mode"] == "fake"
    assert body["units"]["present"] == "kN_m_C"
    assert body["units"]["database"] == "kN_m_C"
    assert body["units"]["length"] == "m"
    assert body["correlation_id"]


def test_joints() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/joints", params={"csys": "Global", "include_restraints": True})
    body = response.json()

    assert response.status_code == 200
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["version_number"] == "0.1.0-fake"
    assert body["adapter_mode"] == "fake"
    assert body["units"]["present"] == "kN_m_C"
    assert len(body["joints"]) == 4
    assert body["joints"][0]["name"] == "J1"
    assert body["joints"][0]["restraint"]["u1"] is True
    assert body["correlation_id"]


def test_no_model_open_error_shape() -> None:
    client = prepared_client(open_model=False)
    response = client.get("/sap2000/model/units")
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["http_status"] == 409
    assert body["error"]["bridge_code"] == "NO_MODEL_OPEN"
    assert body["error"]["message"]
    assert body["error"]["retryable"] is False
    assert body["error"]["correlation_id"]


def test_joints_before_model_open_returns_standard_error() -> None:
    client = prepared_client(open_model=False)
    response = client.get("/sap2000/model/joints")
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["bridge_code"] == "NO_MODEL_OPEN"
    assert body["error"]["correlation_id"]
