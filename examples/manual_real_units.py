"""Manual real-COM smoke: read units from the currently opened SAP2000 model."""

from __future__ import annotations

import json
import os
from urllib import request


BRIDGE_URL = os.environ.get("SAP2000_BRIDGE_URL", "http://127.0.0.1:8000")


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual smoke script.")


def _get(path: str) -> dict[str, object]:
    with request.urlopen(f"{BRIDGE_URL}{path}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    _require_real_com_enabled()
    print("Manual units smoke: this reads units only and does not save or modify a model.")
    print(json.dumps(_get("/sap2000/model/units"), indent=2))


if __name__ == "__main__":
    main()
