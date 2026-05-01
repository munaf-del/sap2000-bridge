import pytest
from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


METADATA_ENDPOINTS = [
    "/sap2000/model/frames",
    "/sap2000/model/materials",
    "/sap2000/model/sections",
    "/sap2000/model/load-patterns",
    "/sap2000/model/load-cases",
    "/sap2000/model/load-combinations",
]


def prepared_client(open_model: bool = True) -> TestClient:
    session_manager.reset()
    client = TestClient(app)
    client.post("/sap2000/connect", json={"attach_to_running": True})
    if open_model:
        client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})
    return client


def assert_metadata_envelope(body: dict) -> None:
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["version_number"] == "0.1.0-fake"
    assert body["adapter_mode"] == "fake"
    assert body["units"]["present"] == "kN_m_C"
    assert body["units"]["database"] == "kN_m_C"
    assert body["correlation_id"]


def test_frames_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/frames", params={"csys": "Global"})
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["frames"] == [
        {"name": "F1", "start_joint": "P1", "end_joint": "P2", "section": "UB310", "coord_system": "Global"},
        {"name": "F2", "start_joint": "P2", "end_joint": "P3", "section": "UB310", "coord_system": "Global"},
    ]


def test_materials_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/materials")
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["materials"] == [
        {"name": "CONC32", "material_type": "Concrete"},
        {"name": "STEEL350", "material_type": "Steel"},
    ]


def test_sections_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/sections")
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["sections"] == [
        {"name": "UB310", "shape_type": "ISection", "material": "STEEL350"},
        {"name": "SLAB150", "shape_type": "Shell/Slab", "material": "CONC32"},
    ]


def test_load_patterns_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/load-patterns")
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["load_patterns"] == [
        {"name": "DEAD", "load_type": "Dead", "self_weight_multiplier": 1.0},
        {"name": "LIVE", "load_type": "Live", "self_weight_multiplier": 0.0},
    ]


def test_load_cases_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/load-cases")
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["load_cases"] == [
        {"name": "DEAD", "case_type": "LinearStatic"},
        {"name": "LIVE", "case_type": "LinearStatic"},
    ]


def test_load_combinations_endpoint_returns_deterministic_fake_data() -> None:
    client = prepared_client()
    response = client.get("/sap2000/model/load-combinations")
    body = response.json()

    assert response.status_code == 200
    assert_metadata_envelope(body)
    assert body["load_combinations"] == [
        {
            "name": "ULS_1",
            "items": [{"name": "DEAD", "scale_factor": 1.2}, {"name": "LIVE", "scale_factor": 1.5}],
        },
        {
            "name": "SLS_1",
            "items": [{"name": "DEAD", "scale_factor": 1.0}, {"name": "LIVE", "scale_factor": 1.0}],
        },
    ]


@pytest.mark.parametrize("endpoint", METADATA_ENDPOINTS)
def test_metadata_endpoints_before_connect_return_standard_error(endpoint: str) -> None:
    session_manager.reset()
    client = TestClient(app)
    response = client.get(endpoint)
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["bridge_code"] == "NOT_CONNECTED"
    assert body["error"]["correlation_id"]


@pytest.mark.parametrize("endpoint", METADATA_ENDPOINTS)
def test_metadata_endpoints_before_model_open_return_standard_error(endpoint: str) -> None:
    client = prepared_client(open_model=False)
    response = client.get(endpoint)
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["bridge_code"] == "NO_MODEL_OPEN"
    assert body["error"]["correlation_id"]
