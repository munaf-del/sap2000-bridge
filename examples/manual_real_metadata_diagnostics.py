"""Manual raw SAP2000 metadata diagnostics.

Attaches to a running SAP2000 instance and prints raw read-only metadata COM
responses. It never launches SAP2000, opens a model, saves, modifies, or runs
analysis.
"""

from __future__ import annotations

import os
from pprint import pprint
import sys


SAP_OBJECT_PROGID = "CSI.SAP2000.API.SapObject"


def _require_real_com_enabled() -> None:
    if os.environ.get("SAP2000_BRIDGE_ENABLE_REAL_COM") != "1":
        raise SystemExit("Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 before running this manual diagnostic script.")


def _print_call(label: str, func) -> None:
    print(f"\n--- {label} ---")
    try:
        result = func()
        pprint(result)
        print("type:", type(result))
    except Exception as exc:
        print("FAIL:", type(exc).__name__, repr(exc))


def main() -> None:
    _require_real_com_enabled()
    if sys.platform != "win32":
        raise SystemExit("Real SAP2000 COM diagnostics must run in native Windows PowerShell.")

    import comtypes
    import comtypes.client

    print("Manual SAP2000 metadata diagnostics. No launch, no open-model, no save, no analysis.")
    comtypes.CoInitialize()
    try:
        helper = comtypes.client.CreateObject("SAP2000v1.Helper")
        sap_object = helper.GetObject(SAP_OBJECT_PROGID)
        model = sap_object.SapModel

        _print_call("FrameObj.GetNameList", lambda: model.FrameObj.GetNameList(0, []))
        _print_call("PropMaterial.GetNameList", lambda: model.PropMaterial.GetNameList(0, []))
        _print_call("PropFrame.GetNameList", lambda: model.PropFrame.GetNameList(0, []))
        _print_call("LoadPatterns.GetNameList", lambda: model.LoadPatterns.GetNameList(0, []))
        _print_call("LoadCases.GetNameList", lambda: model.LoadCases.GetNameList(0, []))
        _print_call("RespCombo.GetNameList", lambda: model.RespCombo.GetNameList(0, []))
    finally:
        comtypes.CoUninitialize()


if __name__ == "__main__":
    main()
