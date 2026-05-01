"""Manual real-COM smoke: list joints from the currently opened SAP2000 model."""

from __future__ import annotations

import json
import os
from urllib import parse, request


BRIDGE_URL = os.environ.get("SAP2000_BRIDGE_URL", "http://127.0.0.1:8000")


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual smoke script.")


def _get(path: str, params: dict[str, object]) -> dict[str, object]:
    query = parse.urlencode(params)
    with request.urlopen(f"{BRIDGE_URL}{path}?{query}", timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    _require_real_com_enabled()
    print("Manual joints smoke: this reads point coordinates only and does not save or modify a model.")
    print(
        json.dumps(
            _get(
                "/sap2000/model/joints",
                {"csys": os.environ.get("SAP2000_CSYS", "Global"), "include_restraints": "false"},
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
