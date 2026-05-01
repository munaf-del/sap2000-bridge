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
    "/sap2000/model/frames",
    "/sap2000/model/materials",
    "/sap2000/model/sections",
    "/sap2000/model/load-patterns",
    "/sap2000/model/load-cases",
    "/sap2000/model/load-combinations",
    "/sap2000/analyze",
    "/sap2000/analyse",
    "/sap2000/analyze/status/{job_id}",
    "/sap2000/analyse/status/{job_id}",
    "/sap2000/results/joint-reactions",
    "/sap2000/results/frame-forces",
    "/sap2000/results/modal-periods",
    "/sap2000/audit",
    "/sap2000/audit/{audit_id}",
    "/sap2000/patches/preview",
    "/sap2000/patches/apply",
}


def test_success_routes_include_correlation_id() -> None:
    session_manager.reset()
    from bridge.services.analysis_runner import analysis_runner

    analysis_runner.reset()
    client = TestClient(app)

    health_response = client.get("/health")
    bridge_info_response = client.get("/bridge/info")
    initial_status_response = client.get("/sap2000/status")
    connect_response = client.post("/sap2000/connect", json={"attach_to_running": True})
    launch_response = client.post("/sap2000/launch", json={"exe_path": None, "visible": True, "startup_delay_s": 0})
    open_model_response = client.post(
        "/sap2000/open-model",
        json={"path": "C:/models/demo.sdb", "copy_to_workspace": False},
    )
    analyze_response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": []})
    analyse_response = client.post("/sap2000/analyse", json={"save_before_run": False, "case_names": []})
    successful_responses = [
        health_response,
        bridge_info_response,
        initial_status_response,
        connect_response,
        launch_response,
        open_model_response,
        client.get("/sap2000/model/units"),
        client.get("/sap2000/model/joints"),
        client.get("/sap2000/model/frames"),
        client.get("/sap2000/model/materials"),
        client.get("/sap2000/model/sections"),
        client.get("/sap2000/model/load-patterns"),
        client.get("/sap2000/model/load-cases"),
        client.get("/sap2000/model/load-combinations"),
        analyze_response,
        client.get(f"/sap2000/analyze/status/{analyze_response.json()['job_id']}"),
        analyse_response,
        client.get(f"/sap2000/analyse/status/{analyse_response.json()['job_id']}"),
        client.get("/sap2000/results/joint-reactions", params={"point_name": "J1"}),
        client.get("/sap2000/results/frame-forces"),
        client.get("/sap2000/results/modal-periods"),
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
