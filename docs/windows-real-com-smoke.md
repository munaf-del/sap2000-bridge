# Windows Real COM Smoke Verification

This is a manual SAP2000 27 smoke path for the local bridge. It is not a CI test path and must never be run by automated pytest.

## Current Scope

Implemented for manual verification:

- Attach to an already-running SAP2000 instance.
- Launch SAP2000 only through `POST /sap2000/launch`.
- Open a local `.sdb` model.
- Read SAP2000 version.
- Read present/database units with raw enum values.
- List joints through the point-object fallback path.

Still not implemented:

- Frame/material/section/load metadata through real COM.
- Real analysis.
- Real result extraction.
- Any model creation, assignment, deletion, modification, save, or write-back.

## Prerequisites

- Windows.
- SAP2000 27 installed at the configured path, normally:

```text
C:\Program Files\Computers and Structures\SAP2000 27
```

- COM registration present for:

```text
SAP2000v1.Helper
CSiAPIv1.Helper
CSI.SAP2000.API.SapObject
```

- `comtypes` installed in the Python environment:

```powershell
python -m pip install -e ".[sap2000]"
```

## Environment Variables

Use fake mode for normal development:

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "fake"
Remove-Item Env:\SAP2000_BRIDGE_ENABLE_REAL_COM -ErrorAction SilentlyContinue
```

Use real COM mode only for manual smoke verification:

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "comtypes"
$env:SAP2000_BRIDGE_ENABLE_REAL_COM = "1"
$env:SAP2000_EXE_PATH = "C:\Program Files\Computers and Structures\SAP2000 27\SAP2000.exe"
$env:SAP2000_MODEL_PATH = "C:\path\to\local\model.sdb"
$env:SAP2000_WORKSPACE = "C:\path\to\sap2000-smoke-workspace"
```

`SAP2000_WORKSPACE` is optional unless you call `/sap2000/open-model` with `copy_to_workspace=true`.

## Run The Bridge In Fake Mode

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "fake"
python -m uvicorn bridge.api.main:app --host 127.0.0.1 --port 8000
```

## Run The Bridge In Real COM Mode

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "comtypes"
$env:SAP2000_BRIDGE_ENABLE_REAL_COM = "1"
python -m uvicorn bridge.api.main:app --host 127.0.0.1 --port 8000
```

If `SAP2000_BRIDGE_ENABLE_REAL_COM` is not `1`, comtypes mode returns `REAL_COM_DISABLED`.

## Attach To Already-Running SAP2000

1. Start SAP2000 manually.
2. Start the bridge in real COM mode.
3. Run:

```powershell
python examples\manual_real_connect.py
```

This calls `POST /sap2000/connect` with `attach_to_running=true`. It does not launch SAP2000 and does not save or modify a model.

## Launch SAP2000

Only use this when you intentionally want the bridge to start SAP2000:

```powershell
python examples\manual_real_launch.py
```

This calls `POST /sap2000/launch`. It does not open, save, or modify a model.

## Open A Copied Local Model

Recommended smoke pattern:

```powershell
$env:SAP2000_MODEL_PATH = "C:\path\to\source\model.sdb"
$env:SAP2000_WORKSPACE = "C:\path\to\sap2000-smoke-workspace"
python examples\manual_real_open_model.py
```

When `SAP2000_WORKSPACE` is set, the manual script asks the bridge to copy the model into that workspace before opening it. The bridge does not save the model.

## Get Units

After connecting or launching and opening a model:

```powershell
python examples\manual_real_units.py
```

The response includes `present_raw` and `database_raw`. Unit enum mapping is intentionally conservative until the SAP2000 27 enum values are fully verified against `CSI_OAPI_Documentation.chm` and `SAP2000v1.tlb`.

## List Joints

After opening a model:

```powershell
python examples\manual_real_joints.py
```

This uses the fallback point-object path. Signature-sensitive calls remain marked in code for verification against the installed CHM/TLB and comtypes tuple/byref behavior.

## Troubleshooting COM Registration

If `ADAPTER_UNAVAILABLE`, `SAP2000_NOT_RUNNING`, or `SAP2000_COM_ERROR` appears:

- Confirm `comtypes` is installed in the active Python environment.
- Confirm SAP2000 27 exists at the configured path.
- Run `GET /bridge/info` and inspect `install_validation`.
- Confirm the COM ProgIDs are registered.
- If registration is missing, use the SAP2000 27 `RegisterSAP2000.exe` repair path manually as an administrator if CSI documentation requires it.

## Revert To Fake Mode

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "fake"
Remove-Item Env:\SAP2000_BRIDGE_ENABLE_REAL_COM -ErrorAction SilentlyContinue
```

Fake mode remains the default and is the only mode used by automated tests.
