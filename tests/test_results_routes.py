from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


def prepared_client() -> TestClient:
    session_manager.adapter.__init__()
    client = TestClient(app)
    client.post("/sap2000/connect", json={"attach_to_running": True})
    client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})
    return client


def test_joint_reactions() -> None:
    client = prepared_client()
    response = client.get(
        "/sap2000/results/joint-reactions",
        params={"point_name": "J1", "case_name": "DEAD", "combo_name": "ULS1"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["units"]["database"] == "N_mm_C"
    assert len(body["rows"]) == 2
    assert body["rows"][0]["obj"] == "J1"
    assert body["rows"][0]["load_case"] == "DEAD"
    assert body["rows"][1]["load_case"] == "ULS1"
    assert body["correlation_id"]


def test_no_writeback_endpoints_enabled() -> None:
    client = prepared_client()
    response = client.post("/sap2000/patches/apply", json={})

    assert response.status_code == 404
