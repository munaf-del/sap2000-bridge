from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.services.session_manager import session_manager


REQUIRED_PATHS = {
    "/health",
    "/bridge/info",
    "/sap2000/status",
    "/sap2000/connect",
    "/sap2000/launch",
    "/sap2000/open-model",
    "/sap2000/model/units",
    "/sap2000/model/joints",
    "/sap2000/analyze",
    "/sap2000/analyse",
    "/sap2000/results/joint-reactions",
}


def test_success_routes_include_correlation_id() -> None:
    session_manager.adapter.__init__()
    client = TestClient(app)

    successful_responses = [
        client.get("/health"),
        client.get("/bridge/info"),
        client.get("/sap2000/status"),
        client.post("/sap2000/connect", json={"attach_to_running": True}),
        client.post("/sap2000/launch", json={"exe_path": None, "visible": True, "startup_delay_s": 0}),
        client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False}),
        client.get("/sap2000/model/units"),
        client.get("/sap2000/model/joints"),
        client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": []}),
        client.post("/sap2000/analyse", json={"save_before_run": False, "case_names": []}),
        client.get("/sap2000/results/joint-reactions", params={"point_name": "J1"}),
    ]

    for response in successful_responses:
        assert response.status_code == 200
        assert response.json()["correlation_id"]


def test_openapi_generation_contains_required_paths() -> None:
    schema = app.openapi()

    assert REQUIRED_PATHS.issubset(set(schema["paths"]))


def test_unknown_path_uses_standard_error_envelope() -> None:
    client = TestClient(app)
    response = client.get("/missing")
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["http_status"] == 404
    assert body["error"]["bridge_code"] == "HTTP_ERROR"
    assert body["error"]["correlation_id"]


def test_request_validation_uses_standard_error_envelope() -> None:
    client = TestClient(app)
    response = client.get("/sap2000/results/joint-reactions")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["http_status"] == 422
    assert body["error"]["bridge_code"] == "VALIDATION_ERROR"
    assert body["error"]["correlation_id"]
