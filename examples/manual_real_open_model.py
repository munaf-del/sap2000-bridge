"""Manual real-COM smoke: open a local .sdb model through the bridge."""

from __future__ import annotations

import json
import os
from urllib import request


BRIDGE_URL = os.environ.get("SAP2000_BRIDGE_URL", "http://127.0.0.1:8000")


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual smoke script.")


def _require_model_path() -> str:
    model_path = os.environ.get("SAP2000_MODEL_PATH")
    if not model_path:
        raise SystemExit("Set SAP2000_MODEL_PATH to a local .sdb file before running this script.")
    return model_path


def _post(path: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BRIDGE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    _require_real_com_enabled()
    model_path = _require_model_path()
    copy_to_workspace = bool(os.environ.get("SAP2000_WORKSPACE"))
    print("Manual open-model smoke: the bridge opens the model and never saves or modifies it.")
    if copy_to_workspace:
        print("SAP2000_WORKSPACE is set, so the bridge will open a copied model file.")
    print(
        json.dumps(
            _post(
                "/sap2000/open-model",
                {"path": model_path, "copy_to_workspace": copy_to_workspace},
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
