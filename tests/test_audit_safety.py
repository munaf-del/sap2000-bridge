import inspect

from fastapi.testclient import TestClient

from bridge.adapters.fake_adapter import FakeSapAdapter
from bridge.api.main import app
from bridge.services.audit import audit_service
from bridge.services.session_manager import session_manager


def fresh_client() -> TestClient:
    session_manager.reset()
    audit_service.clear()
    return TestClient(app)


def test_audit_records_successful_routes() -> None:
    client = fresh_client()
    response = client.get("/health", headers={"X-Correlation-ID": "audit-success-001"})

    assert response.status_code == 200
    records = audit_service.list_records()
    assert len(records) == 1
    assert records[0].correlation_id == "audit-success-001"
    assert records[0].method == "GET"
    assert records[0].route == "/health"
    assert records[0].status == "succeeded"
    assert records[0].adapter_mode == "fake"


def test_audit_records_error_routes() -> None:
    client = fresh_client()
    response = client.get(
        "/sap2000/model/units",
        headers={"X-Correlation-ID": "audit-error-001"},
    )

    assert response.status_code == 409
    records = audit_service.list_records()
    assert len(records) == 1
    assert records[0].correlation_id == "audit-error-001"
    assert records[0].route == "/sap2000/model/units"
    assert records[0].status == "failed"
    assert records[0].bridge_code == "NOT_CONNECTED"
    assert records[0].sap_ret is None


def test_audit_list_and_get_by_id() -> None:
    client = fresh_client()
    client.get("/health")
    audit_id = audit_service.list_records()[0].audit_id

    list_response = client.get("/sap2000/audit")
    list_body = list_response.json()
    get_response = client.get(f"/sap2000/audit/{audit_id}")
    get_body = get_response.json()

    assert list_response.status_code == 200
    assert any(record["audit_id"] == audit_id for record in list_body["records"])
    assert list_body["correlation_id"]
    assert get_response.status_code == 200
    assert get_body["record"]["audit_id"] == audit_id
    assert get_body["correlation_id"]


def test_unknown_audit_id_returns_standard_error() -> None:
    client = fresh_client()
    response = client.get("/sap2000/audit/missing")
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["http_status"] == 404
    assert body["error"]["bridge_code"] == "UNKNOWN_AUDIT_RECORD"
    assert body["error"]["correlation_id"]


def test_writeback_preview_and_apply_are_disabled() -> None:
    client = fresh_client()
    responses = [
        client.post("/sap2000/patches/preview", json={}),
        client.post("/sap2000/patches/apply", json={}),
    ]

    for response in responses:
        body = response.json()
        assert response.status_code == 501
        assert body["error"]["http_status"] == 501
        assert body["error"]["bridge_code"] == "WRITEBACK_DISABLED"
        assert body["error"]["retryable"] is False
        assert body["error"]["correlation_id"]


def test_disabled_writeback_does_not_modify_model_state() -> None:
    client = fresh_client()
    client.post("/sap2000/connect", json={"attach_to_running": True})
    client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})

    before = client.get("/sap2000/status").json()
    response = client.post("/sap2000/patches/apply", json={"anything": "ignored"})
    after = client.get("/sap2000/status").json()

    assert response.status_code == 501
    assert before["model_path"] == after["model_path"] == "C:/models/demo.sdb"
    assert before["model_name"] == after["model_name"] == "demo.sdb"
    assert before["model_open"] is after["model_open"] is True


def test_fake_adapter_has_no_model_mutation_methods() -> None:
    forbidden_fragments = ("save", "write", "assign", "delete", "modify", "create_model", "set_model")
    method_names = [
        name.lower()
        for name, value in inspect.getmembers(FakeSapAdapter, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]

    assert not [name for name in method_names if any(fragment in name for fragment in forbidden_fragments)]


def test_openapi_includes_disabled_writeback_only_as_disabled_endpoints() -> None:
    schema = app.openapi()
    patch_paths = {path for path in schema["paths"] if path.startswith("/sap2000/patches")}

    assert patch_paths == {"/sap2000/patches/preview", "/sap2000/patches/apply"}
    assert set(schema["paths"]["/sap2000/patches/preview"]) == {"post"}
    assert set(schema["paths"]["/sap2000/patches/apply"]) == {"post"}
