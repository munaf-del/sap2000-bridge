"""Manual real-COM smoke: attach to an already-running SAP2000 instance.

Start the bridge separately with:
SAP2000_BRIDGE_ADAPTER_MODE=comtypes
SAP2000_BRIDGE_ENABLE_REAL_COM=1
"""

from __future__ import annotations

import json
import os
from urllib import request


BRIDGE_URL = os.environ.get("SAP2000_BRIDGE_URL", "http://127.0.0.1:8765")


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual smoke script.")


def _post(path: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BRIDGE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    _require_real_com_enabled()
    print("Manual attach smoke: SAP2000 must already be running. This script does not save or modify a model.")
    print(json.dumps(_post("/sap2000/connect", {"attach_to_running": True}), indent=2))


if __name__ == "__main__":
    main()
