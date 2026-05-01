"""Manual attach diagnostics for SAP2000 real-COM mode.

This script never launches SAP2000, never opens a model, and never saves or
modifies anything. It only verifies helper creation, attach, and SapModel access.
"""

from __future__ import annotations

import os
import sys


HELPER_PROGIDS = ("SAP2000v1.Helper", "CSiAPIv1.Helper")
SAP_OBJECT_PROGID = "CSI.SAP2000.API.SapObject"


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual diagnostic script.")


def main() -> None:
    _require_real_com_enabled()
    if sys.platform != "win32":
        raise SystemExit("Real SAP2000 COM diagnostics must run in native Windows PowerShell.")

    import comtypes
    import comtypes.client

    print("Manual SAP2000 attach diagnostics. No launch, no open-model, no save.")
    comtypes.CoInitialize()
    try:
        for helper_progid in HELPER_PROGIDS:
            print(f"\nHelper ProgID: {helper_progid}")
            try:
                helper = comtypes.client.CreateObject(helper_progid)
                print("  helper create: OK")
            except Exception as exc:
                print(f"  helper create: FAIL {exc!r}")
                continue

            try:
                sap_object = helper.GetObject(SAP_OBJECT_PROGID)
                print("  Helper.GetObject: OK")
            except Exception as exc:
                print(f"  Helper.GetObject: FAIL {exc!r}")
                continue

            try:
                sap_model = sap_object.SapModel
                print(f"  SapModel: OK {sap_model!r}")
            except Exception as exc:
                print(f"  SapModel: FAIL {exc!r}")
    finally:
        comtypes.CoUninitialize()


if __name__ == "__main__":
    main()
