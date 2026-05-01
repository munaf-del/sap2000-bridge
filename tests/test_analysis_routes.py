from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


def prepared_client() -> TestClient:
    session_manager.adapter.__init__()
    client = TestClient(app)
    client.post("/sap2000/connect", json={"attach_to_running": True})
    client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})
    return client


def test_analyze() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": []})
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"].startswith("fake-analysis-")
    assert body["state"] == "completed"
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["version_number"] == "0.1.0-fake"
    assert body["adapter_mode"] == "fake"
    assert body["submitted_at_utc"]
    assert body["started_at_utc"]
    assert body["finished_at_utc"]
    assert body["correlation_id"]


def test_analyse_alias() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyse", json={"save_before_run": False, "case_names": []})
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"].startswith("fake-analysis-")
    assert body["state"] == "completed"
    assert body["correlation_id"]


def test_save_before_run_is_disabled() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyze", json={"save_before_run": True, "case_names": []})
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["bridge_code"] == "READ_ONLY_VIOLATION"
    assert body["error"]["correlation_id"]
