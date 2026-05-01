from __future__ import annotations

import json
from typing import Any
from urllib import parse, request


class Sap2000BridgeAgentClient:
    """Restricted client for runtime agents that may only call approved endpoints."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765", timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def bridge_info(self) -> dict[str, Any]:
        return self._get("/bridge/info")

    def status(self) -> dict[str, Any]:
        return self._get("/sap2000/status")

    def connect(self, attach_to_running: bool = True) -> dict[str, Any]:
        return self._post("/sap2000/connect", {"attach_to_running": attach_to_running})

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> dict[str, Any]:
        return self._post(
            "/sap2000/launch",
            {"exe_path": exe_path, "visible": visible, "startup_delay_s": startup_delay_s},
        )

    def open_model(self, path: str, copy_to_workspace: bool = False) -> dict[str, Any]:
        return self._post("/sap2000/open-model", {"path": path, "copy_to_workspace": copy_to_workspace})

    def get_units(self) -> dict[str, Any]:
        return self._get("/sap2000/model/units")

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> dict[str, Any]:
        return self._get(
            "/sap2000/model/joints",
            {"csys": csys, "include_restraints": str(include_restraints).lower()},
        )

    def list_frames(self, csys: str = "Global") -> dict[str, Any]:
        return self._get("/sap2000/model/frames", {"csys": csys})

    def list_materials(self) -> dict[str, Any]:
        return self._get("/sap2000/model/materials")

    def list_sections(self) -> dict[str, Any]:
        return self._get("/sap2000/model/sections")

    def list_load_patterns(self) -> dict[str, Any]:
        return self._get("/sap2000/model/load-patterns")

    def list_load_cases(self) -> dict[str, Any]:
        return self._get("/sap2000/model/load-cases")

    def list_load_combinations(self) -> dict[str, Any]:
        return self._get("/sap2000/model/load-combinations")

    def analyze(self, save_before_run: bool = False, case_names: list[str] | None = None) -> dict[str, Any]:
        return self._post(
            "/sap2000/analyze",
            {"save_before_run": save_before_run, "case_names": case_names or []},
        )

    def analysis_status(self, job_id: str) -> dict[str, Any]:
        return self._get(f"/sap2000/analyze/status/{parse.quote(job_id, safe='')}")

    def joint_reactions(
        self,
        point_name: str,
        case_name: str | None = None,
        combo_name: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none({"point_name": point_name, "case_name": case_name, "combo_name": combo_name})
        return self._get("/sap2000/results/joint-reactions", params)

    def frame_forces(
        self,
        frame_name: str | None = None,
        case_name: str | None = None,
        combo_name: str | None = None,
    ) -> dict[str, Any]:
        params = _drop_none({"frame_name": frame_name, "case_name": case_name, "combo_name": combo_name})
        return self._get("/sap2000/results/frame-forces", params)

    def modal_periods(self, case_name: str | None = None) -> dict[str, Any]:
        return self._get("/sap2000/results/modal-periods", _drop_none({"case_name": case_name}))

    def audit_list(self) -> dict[str, Any]:
        return self._get("/sap2000/audit")

    def audit_get(self, audit_id: str) -> dict[str, Any]:
        return self._get(f"/sap2000/audit/{parse.quote(audit_id, safe='')}")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(path, params)
        with request.urlopen(url, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self._url(path),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout_s) as response:
            return json.loads(response.read().decode("utf-8"))

    def _url(self, path: str, params: dict[str, Any] | None = None) -> str:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{parse.urlencode(params)}"
        return url


def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
