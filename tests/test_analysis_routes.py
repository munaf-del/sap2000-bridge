from datetime import datetime, timezone

from fastapi.testclient import TestClient

from bridge.api.main import app
from bridge.contracts.results import AnalysisJobStatus
from bridge.services.analysis_runner import analysis_runner
from bridge.services.session_manager import session_manager


def prepared_client() -> TestClient:
    session_manager.reset()
    analysis_runner.reset()
    client = TestClient(app)
    client.post("/sap2000/connect", json={"attach_to_running": True})
    client.post("/sap2000/open-model", json={"path": "C:/models/demo.sdb", "copy_to_workspace": False})
    return client


def test_analyze() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": []})
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"].startswith("analysis-")
    assert body["state"] == "succeeded"
    assert body["model_path"] == "C:/models/demo.sdb"
    assert body["model_name"] == "demo.sdb"
    assert body["version_label"] == "SAP2000 Fake Adapter v0.1"
    assert body["version_number"] == "0.1.0-fake"
    assert body["adapter_mode"] == "fake"
    assert body["submitted_at_utc"]
    assert body["started_at_utc"]
    assert body["finished_at_utc"]
    assert body["case_status"] == {"ALL": "succeeded"}
    assert body["correlation_id"]


def test_analyse_alias() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyse", json={"save_before_run": False, "case_names": []})
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"].startswith("analysis-")
    assert body["state"] == "succeeded"
    assert body["correlation_id"]


def test_analysis_status_lookup_works() -> None:
    client = prepared_client()
    create_response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": ["DEAD"]})
    job_id = create_response.json()["job_id"]
    response = client.get(f"/sap2000/analyze/status/{job_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"] == job_id
    assert body["state"] == "succeeded"
    assert body["case_status"] == {"DEAD": "succeeded"}
    assert body["correlation_id"]


def test_analysis_status_alias_works() -> None:
    client = prepared_client()
    create_response = client.post("/sap2000/analyse", json={"save_before_run": False, "case_names": ["LIVE"]})
    job_id = create_response.json()["job_id"]
    response = client.get(f"/sap2000/analyse/status/{job_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["job_id"] == job_id
    assert body["state"] == "succeeded"
    assert body["case_status"] == {"LIVE": "succeeded"}
    assert body["correlation_id"]


def test_unknown_analysis_job_returns_standard_error() -> None:
    client = prepared_client()
    response = client.get("/sap2000/analyze/status/missing-job")
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["http_status"] == 404
    assert body["error"]["bridge_code"] == "UNKNOWN_ANALYSIS_JOB"
    assert body["error"]["correlation_id"]


def test_failed_job_simulation() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": ["__FAIL__"]})
    body = response.json()

    assert response.status_code == 200
    assert body["state"] == "failed"
    assert body["case_status"] == {"__FAIL__": "failed"}
    assert body["error_message"] == "Fake analysis failure requested by __FAIL__ case name."
    assert body["correlation_id"]


def test_second_job_while_running_returns_standard_error() -> None:
    client = prepared_client()
    active_job = AnalysisJobStatus(
        job_id="analysis-active",
        state="running",
        model_path="C:/models/demo.sdb",
        model_name="demo.sdb",
        version_label="SAP2000 Fake Adapter v0.1",
        version_number="0.1.0-fake",
        adapter_mode="fake",
        submitted_at_utc=datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
        started_at_utc=datetime(2026, 5, 1, 0, 0, 1, tzinfo=timezone.utc),
        case_status={"ALL": "running"},
    )
    analysis_runner._jobs[active_job.job_id] = active_job
    analysis_runner._active_job_id = active_job.job_id

    try:
        response = client.post("/sap2000/analyze", json={"save_before_run": False, "case_names": []})
        body = response.json()

        assert response.status_code == 409
        assert body["error"]["http_status"] == 409
        assert body["error"]["bridge_code"] == "ANALYSIS_ALREADY_RUNNING"
        assert body["error"]["retryable"] is True
        assert body["error"]["correlation_id"]
    finally:
        analysis_runner.reset()


def test_save_before_run_is_disabled() -> None:
    client = prepared_client()
    response = client.post("/sap2000/analyze", json={"save_before_run": True, "case_names": []})
    body = response.json()

    assert response.status_code == 409
    assert body["error"]["bridge_code"] == "READ_ONLY_VIOLATION"
    assert body["error"]["correlation_id"]
