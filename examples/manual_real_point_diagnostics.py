"""Manual SAP2000 point diagnostics for real-COM smoke verification.

This script attaches to a running SAP2000 instance and prints raw read-only COM
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


def _candidate_names(names_result) -> list[str]:
    candidates: list[str] = []
    if isinstance(names_result, (list, tuple)):
        for item in names_result:
            if isinstance(item, (list, tuple)):
                candidates.extend(str(name) for name in item)
            elif isinstance(item, str):
                candidates.append(item)
    return list(dict.fromkeys(candidates))[:5]


def main() -> None:
    _require_real_com_enabled()
    if sys.platform != "win32":
        raise SystemExit("Real SAP2000 COM diagnostics must run in native Windows PowerShell.")

    import comtypes
    import comtypes.client

    print("Manual SAP2000 point diagnostics. No launch, no open-model, no save, no analysis.")
    print("Python:", sys.executable)
    comtypes.CoInitialize()
    try:
        helper = comtypes.client.CreateObject("SAP2000v1.Helper")
        sap_object = helper.GetObject(SAP_OBJECT_PROGID)
        model = sap_object.SapModel

        print("\n--- Version ---")
        try:
            version = model.GetVersion("", 0.0)
            print("GetVersion raw:")
            pprint(version)
            print("type:", type(version))
        except Exception as exc:
            print("GetVersion FAIL:", type(exc).__name__, repr(exc))

        print("\n--- Units ---")
        try:
            print("GetPresentUnits raw:", repr(model.GetPresentUnits()))
            print("GetDatabaseUnits raw:", repr(model.GetDatabaseUnits()))
        except Exception as exc:
            print("Units FAIL:", type(exc).__name__, repr(exc))

        print("\n--- PointObj.GetNameList ---")
        names_result = None
        try:
            names_result = model.PointObj.GetNameList(0, [])
            print("GetNameList raw:")
            pprint(names_result)
            print("type:", type(names_result))
        except Exception as exc:
            print("GetNameList FAIL:", type(exc).__name__, repr(exc))

        print("\n--- PointObj.GetAllPoints ---")
        try:
            all_points = model.PointObj.GetAllPoints(0, [], [], [], [], "Global")
            print("GetAllPoints raw:")
            pprint(all_points)
            print("type:", type(all_points))
        except Exception as exc:
            print("GetAllPoints FAIL:", type(exc).__name__, repr(exc))

        print("\n--- PointObj.GetCoordCartesian ---")
        for name in _candidate_names(names_result):
            print(f"\nPoint name: {name!r}")
            try:
                coord = model.PointObj.GetCoordCartesian(str(name), 0.0, 0.0, 0.0, "Global")
                print("GetCoordCartesian raw:")
                pprint(coord)
                print("type:", type(coord))
            except Exception as exc:
                print("GetCoordCartesian FAIL:", type(exc).__name__, repr(exc))
    finally:
        comtypes.CoUninitialize()


if __name__ == "__main__":
    main()
