"""Manual real-COM smoke: launch SAP2000 through the local bridge."""

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
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    _require_real_com_enabled()
    print("Manual launch smoke: this starts SAP2000 but does not open, save, or modify a model.")
    print(
        json.dumps(
            _post(
                "/sap2000/launch",
                {
                    "exe_path": os.environ.get("SAP2000_EXE_PATH"),
                    "visible": True,
                    "startup_delay_s": 5.0,
                },
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
