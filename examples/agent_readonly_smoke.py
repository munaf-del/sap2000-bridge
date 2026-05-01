"""Run the approved read-only bridge smoke through the restricted agent client."""

from __future__ import annotations

import json
from typing import Any

from bridge.agent_client import Sap2000BridgeAgentClient


MODEL_PATH = r"C:\SAP2000BridgeWorkspace\smoke_frame_2point.sdb"


def _count(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key) or []
    return len(value)


def main() -> None:
    client = Sap2000BridgeAgentClient()
    errors: list[str] = []

    try:
        client.health()
        info = client.bridge_info()
        client.status()
        connect = client.connect(attach_to_running=True)
        open_model = client.open_model(MODEL_PATH, copy_to_workspace=False)
        units = client.get_units()
        joints = client.list_joints()
        frames = client.list_frames()
        materials = client.list_materials()
        sections = client.list_sections()
        patterns = client.list_load_patterns()
        cases = client.list_load_cases()
        combinations = client.list_load_combinations()
        audit = client.audit_list()
    except Exception as exc:
        errors.append(str(exc))
        summary = {"errors": errors}
    else:
        summary = {
            "adapter_mode": info.get("adapter_mode"),
            "sap2000_version": connect.get("version_label"),
            "model_path": open_model.get("model_path"),
            "units": (units.get("units") or {}).get("present"),
            "joint_count": _count(joints, "joints"),
            "frame_count": _count(frames, "frames"),
            "material_count": _count(materials, "materials"),
            "section_count": _count(sections, "sections"),
            "load_pattern_count": _count(patterns, "load_patterns"),
            "load_case_count": _count(cases, "load_cases"),
            "load_combination_count": _count(combinations, "load_combinations"),
            "audit_count": _count(audit, "records"),
            "errors": errors,
        }

    print(json.dumps(summary, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

