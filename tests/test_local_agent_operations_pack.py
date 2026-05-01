import inspect
from pathlib import Path

from fastapi.testclient import TestClient

from bridge.agent_client import Sap2000BridgeAgentClient
from bridge.api.main import app


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def public_client_methods() -> set[str]:
    return {
        name
        for name, value in inspect.getmembers(Sap2000BridgeAgentClient, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_local_agent_operations_files_exist() -> None:
    for relative in [
        "docs/local-agent-operations.md",
        "docs/openclaw-runtime-bridge-agent.md",
        "docs/codex-agent-playbook.md",
        "prompts/openclaw-runtime-readonly.txt",
        "prompts/codex-verification-agent.txt",
        "scripts/start_bridge_fake.ps1",
        "scripts/start_bridge_comtypes.ps1",
        "scripts/stop_bridge.ps1",
        "scripts/agent_readonly_smoke.ps1",
        "examples/agent_readonly_smoke.py",
    ]:
        assert (ROOT / relative).is_file()


def test_scripts_use_loopback_bridge_port_and_not_external_bind_literal() -> None:
    for relative in [
        "scripts/start_bridge_fake.ps1",
        "scripts/start_bridge_comtypes.ps1",
        "scripts/stop_bridge.ps1",
        "scripts/agent_readonly_smoke.ps1",
    ]:
        text = read(relative)
        assert "127.0.0.1" in text
        assert "8765" in text
        assert "0.0.0.0" not in text


def test_agent_smoke_scripts_do_not_call_analysis_results_or_writeback() -> None:
    for relative in ["scripts/agent_readonly_smoke.ps1", "examples/agent_readonly_smoke.py"]:
        text = read(relative).lower()
        forbidden_endpoints = [
            "/sap2000/analyze",
            "/sap2000/analyse",
            "/sap2000/results",
            "/sap2000/patches",
        ]
        for endpoint in forbidden_endpoints:
            assert endpoint not in text
        assert "patch_apply" not in text
        assert "patch_preview" not in text
        assert "raw_request" not in text


def test_agent_client_still_has_no_raw_request_or_writeback_methods() -> None:
    methods = public_client_methods()
    forbidden = {
        "raw_request",
        "patch_preview",
        "patch_apply",
        "writeback",
        "save",
        "modify",
        "assign",
        "delete",
    }

    assert forbidden.isdisjoint(methods)
    assert not [name for name in methods if "patch" in name or "writeback" in name]


def test_operations_docs_and_prompts_include_forbidden_actions() -> None:
    combined = "\n".join(
        read(relative)
        for relative in [
            "docs/local-agent-operations.md",
            "docs/openclaw-runtime-bridge-agent.md",
            "docs/codex-agent-playbook.md",
            "prompts/openclaw-runtime-readonly.txt",
            "prompts/codex-verification-agent.txt",
        ]
    ).lower()

    for phrase in [
        "direct SAP2000 COM/OAPI",
        "direct .sdb",
        "write-back",
        "patch/apply",
        "create, modify, delete, assign, save",
        "real analysis is not implemented",
        "real result extraction is not implemented",
        "http://127.0.0.1:8765",
    ]:
        assert phrase.lower() in combined


def test_disabled_writeback_endpoints_remain_501_only() -> None:
    client = TestClient(app)

    for path in ["/sap2000/patches/preview", "/sap2000/patches/apply"]:
        response = client.post(path, json={})
        body = response.json()

        assert response.status_code == 501
        assert body["error"]["bridge_code"] == "WRITEBACK_DISABLED"
        assert body["error"]["retryable"] is False

    openapi = client.get("/openapi.json").json()
    assert "/sap2000/patches/preview" in openapi["paths"]
    assert "/sap2000/patches/apply" in openapi["paths"]
