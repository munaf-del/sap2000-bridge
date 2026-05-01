"""Manual bridge call: read SAP2000 load pattern metadata."""

from __future__ import annotations

import json
import os
from urllib import request


BRIDGE_URL = os.environ.get("SAP2000_BRIDGE_URL", "http://127.0.0.1:8765")


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual script.")


def main() -> None:
    _require_real_com_enabled()
    print("Manual load-pattern metadata smoke. No save, no modification, no analysis.")
    with request.urlopen(f"{BRIDGE_URL}/sap2000/model/load-patterns", timeout=60) as response:
        print(json.dumps(json.loads(response.read().decode("utf-8")), indent=2))


if __name__ == "__main__":
    main()
