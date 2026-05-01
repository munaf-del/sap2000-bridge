import inspect
from pathlib import Path
from typing import Any

from bridge.agent_client import Sap2000BridgeAgentClient


class RecordingAgentClient(Sap2000BridgeAgentClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://bridge.test")
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(("GET", path, params))
        return {"ok": True}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("POST", path, payload))
        return {"ok": True}


def public_client_methods() -> set[str]:
    return {
        name
        for name, value in inspect.getmembers(Sap2000BridgeAgentClient, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_agent_client_has_no_writeback_or_raw_escape_methods() -> None:
    methods = public_client_methods()
    forbidden = {
        "patch_preview",
        "patch_apply",
        "save",
        "modify",
        "assign",
        "delete",
        "raw_request",
    }

    assert forbidden.isdisjoint(methods)
    assert not [name for name in methods if "patch" in name or "writeback" in name]


def test_agent_client_allowed_methods_call_correct_endpoints() -> None:
    client = RecordingAgentClient()

    client.health()
    client.bridge_info()
    client.status()
    client.connect()
    client.launch(startup_delay_s=0)
    client.open_model("C:/models/demo.sdb")
    client.get_units()
    client.list_joints()
    client.list_frames()
    client.list_materials()
    client.list_sections()
    client.list_load_patterns()
    client.list_load_cases()
    client.list_load_combinations()
    client.analyze(case_names=["DEAD"])
    client.analysis_status("job 1")
    client.joint_reactions(point_name="J1", case_name="DEAD")
    client.frame_forces(frame_name="F1", combo_name="ULS_1")
    client.modal_periods(case_name="MODAL")
    client.audit_list()
    client.audit_get("audit 1")

    assert client.calls == [
        ("GET", "/health", None),
        ("GET", "/bridge/info", None),
        ("GET", "/sap2000/status", None),
        ("POST", "/sap2000/connect", {"attach_to_running": True}),
        ("POST", "/sap2000/launch", {"exe_path": None, "visible": True, "startup_delay_s": 0}),
        ("POST", "/sap2000/open-model", {"path": "C:/models/demo.sdb", "copy_to_workspace": False}),
        ("GET", "/sap2000/model/units", None),
        ("GET", "/sap2000/model/joints", {"csys": "Global", "include_restraints": "false"}),
        ("GET", "/sap2000/model/frames", {"csys": "Global"}),
        ("GET", "/sap2000/model/materials", None),
        ("GET", "/sap2000/model/sections", None),
        ("GET", "/sap2000/model/load-patterns", None),
        ("GET", "/sap2000/model/load-cases", None),
        ("GET", "/sap2000/model/load-combinations", None),
        ("POST", "/sap2000/analyze", {"save_before_run": False, "case_names": ["DEAD"]}),
        ("GET", "/sap2000/analyze/status/job%201", None),
        ("GET", "/sap2000/results/joint-reactions", {"point_name": "J1", "case_name": "DEAD"}),
        ("GET", "/sap2000/results/frame-forces", {"frame_name": "F1", "combo_name": "ULS_1"}),
        ("GET", "/sap2000/results/modal-periods", {"case_name": "MODAL"}),
        ("GET", "/sap2000/audit", None),
        ("GET", "/sap2000/audit/audit%201", None),
    ]


def test_agent_policy_file_exists_and_contains_safety_rules() -> None:
    policy_path = Path(__file__).resolve().parents[1] / "docs" / "agent-policy.md"
    text = policy_path.read_text(encoding="utf-8")

    assert "Coding Agent" in text
    assert "Verification Agent" in text
    assert "Runtime Bridge Agent" in text
    assert "direct SAP2000 COM access" in text
    assert "direct COM/OAPI" in text
    assert "direct `.sdb` editing" in text
    assert "writeback endpoints" in text
    assert "patch/apply" in text
    assert "interpreting results without units" in text


def test_agent_policy_contains_human_approval_rules() -> None:
    policy_path = Path(__file__).resolve().parents[1] / "docs" / "agent-policy.md"
    text = policy_path.read_text(encoding="utf-8")

    for phrase in [
        "launching SAP2000",
        "opening a model",
        "running analysis",
        "uploading or exporting results",
        "switching from fake mode to comtypes mode",
    ]:
        assert phrase in text


def test_checkpoint_workflow_documents_fast_checkpoint_process() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / "docs" / "checkpoint-workflow.md"
    text = workflow_path.read_text(encoding="utf-8")

    assert "Marty is the sole developer" in text
    assert "GitHub is backup and revision history" in text
    assert "slow PR gate" in text
    assert "pytest -q" in text
    assert "git status" in text
    assert "git add -A" in text
    assert 'git commit -m "checkpoint-XX-description"' in text
    assert "git push" in text
    assert "Do not push a checkpoint until the test suite passes" in text
