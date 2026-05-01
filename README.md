# SAP2000 Local Bridge

This repository is the first read-only Python/FastAPI bridge for connecting a SaaS or AI engineering platform to SAP2000 running locally on Windows.

The bridge exposes a narrow HTTP API on `127.0.0.1`, calls through a `SapAdapter` interface, and uses a deterministic `FakeSapAdapter` for tests. The future `ComtypesSapAdapter` is present only as a clearly marked placeholder until the exact SAP2000 OAPI signatures are verified against the installed SAP2000 API CHM, TLB, or DLLs.

## Architecture

```text
SaaS / AI Agent / Codex
  -> localhost FastAPI bridge
  -> SapAdapter interface
  -> FakeSapAdapter for tests
  -> future ComtypesSapAdapter for real SAP2000
  -> SAP2000 desktop application
  -> .sdb model files
```

## Why Local-Only

SAP2000 is a Windows desktop application and current bridge control should happen on the same machine as SAP2000. The API binds to localhost only in normal use and must not be exposed as a network service.

## MVP Scope

The MVP is read-only except for triggering analysis. It can connect, launch, open a local `.sdb` path, read units, list joints, run analysis, and read joint reactions through approved endpoints.

No model write-back is implemented. No route creates, modifies, assigns, deletes, or saves SAP2000 model data.

## Endpoints

- `GET /health`
- `GET /bridge/info`
- `GET /sap2000/status`
- `POST /sap2000/connect`
- `POST /sap2000/launch`
- `POST /sap2000/open-model`
- `GET /sap2000/model/units`
- `GET /sap2000/model/joints`
- `GET /sap2000/model/frames`
- `GET /sap2000/model/materials`
- `GET /sap2000/model/sections`
- `GET /sap2000/model/load-patterns`
- `GET /sap2000/model/load-cases`
- `GET /sap2000/model/load-combinations`
- `POST /sap2000/analyze`
- `POST /sap2000/analyse`
- `GET /sap2000/analyze/status/{job_id}`
- `GET /sap2000/analyse/status/{job_id}`
- `GET /sap2000/results/joint-reactions`
- `GET /sap2000/results/frame-forces`
- `GET /sap2000/results/modal-periods`

AI agents must call only these approved bridge endpoints in the MVP.

`GET /bridge/info` also reports `sap2000_target`, a read-only validation summary for the configured local SAP2000 install. This is used to confirm the bridge is pointed at SAP2000 27 before the real adapter is implemented.

## Contract Hardening

All successful API responses are backed by Pydantic response models and include a `correlation_id`. SAP/model/result responses carry adapter and model context where applicable, including `adapter_mode`, `model_path`, `model_name`, `version_label`, `version_number`, and present/database units.

Errors use one standard envelope:

```json
{
  "error": {
    "http_status": 409,
    "bridge_code": "NO_MODEL_OPEN",
    "message": "...",
    "sap_ret": null,
    "sap_context": null,
    "retryable": false,
    "correlation_id": "..."
  }
}
```

`GET /bridge/info` includes both `sap2000_target` path metadata and `install_validation` readiness flags for SAP2000 27. The validator is safe on machines without SAP2000 installed: missing files and COM registration are reported as false with warnings instead of crashing imports.

## Analysis Jobs

`POST /sap2000/analyze` and `POST /sap2000/analyse` are spelling aliases. They create a serial analysis job and return its lifecycle state. The current fake adapter completes jobs immediately through `queued`, `running`, then `succeeded` or `failed`; only one active job may run at a time.

Job status can be read from either alias:

- `GET /sap2000/analyze/status/{job_id}`
- `GET /sap2000/analyse/status/{job_id}`

Real SAP2000 analysis is not implemented yet. The future COM adapter still contains placeholders only and must verify `Analyze.RunAnalysis` and any case-status calls against the installed SAP2000 27 API documentation and type library before use.

## Results

The MVP exposes read-only result endpoints for joint reactions, frame forces, and modal periods. Current responses are deterministic fake data for contract testing. Real result extraction remains placeholder-only until SAP2000 27 COM signatures are manually verified for result setup selection and result array/byref behavior.

## Setup

```powershell
cd sap2000-bridge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

`comtypes` is optional and Windows-only:

```powershell
python -m pip install -e ".[sap2000]"
```

Tests and normal imports do not require SAP2000 or `comtypes`.

## Test

```powershell
pytest -q
```

## Run The API

```powershell
python -m uvicorn bridge.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

## Windows And SAP2000 Notes

The fake adapter is the default so the app imports cleanly on non-Windows machines. Real SAP2000 control must be added gradually in `ComtypesSapAdapter` only after checking the installed SAP2000 API documentation on the target Windows machine.

This machine has SAP2000 27 installed at:

```text
C:\Program Files\Computers and Structures\SAP2000 27
```

The wider CSI products root is:

```text
C:\Program Files\Computers and Structures
```

Installed product folders observed there:

- `CSiXCAD 19`
- `CSiXRevit 2023`
- `CSiXRevit 2025`
- `CSiXRevit 2026`
- `SAP2000 24`
- `SAP2000 25`
- `SAP2000 26`
- `SAP2000 27`

SAP2000 25, 26, and 27 folders each include `SAP2000.exe`, `SAP2000v1.dll`, `CSiAPIv1.dll`, `CSI_OAPI_Documentation.chm`, and `SAP2000.chm` in the root. SAP2000 27 is the latest installed SAP2000 version and the configured bridge target.

The following files were found there during the initial read-only check:

- `SAP2000.exe`
- `SAP2000v1.dll`
- `CSiAPIv1.dll`
- `CSI_OAPI_Documentation.chm`
- `SAP2000.chm`

Additional compatibility artefacts found for SAP2000 27:

- `SAP2000.runtimeconfig.json`
- `SAP2000.deps.json`
- `RegisterSAP2000.exe`
- `UnregisterSAP2000.exe`
- `NativeAPI`

Read-only registry checks also found the expected COM ProgIDs:

- `SAP2000v1.Helper`
- `CSiAPIv1.Helper`
- `CSI.SAP2000.API.SapObject`

The default config records those paths, but the app still uses the fake adapter unless `SAP2000_BRIDGE_ADAPTER_MODE=comtypes` is set. Real COM calls remain placeholders.

Before implementing real calls, verify:

- helper creation;
- attach to running SAP2000;
- create/launch SAP2000;
- open model;
- get version;
- get present units;
- get database units;
- list joints;
- run analysis;
- extract joint reactions;
- `comtypes` tuple/byref behavior;
- all SAP return-code shapes.

Every SAP return code must go through `check_ret`.

## Write-Back Warning

Real write-back is intentionally disabled. Future write-back requires preview, explicit human approval, backup, validation, and audit records before any model mutation endpoint is enabled.

The COM adapter contains placeholders only. Do not treat those placeholders as final SAP2000 API signatures.
