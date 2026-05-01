# OpenClaw Runtime Bridge Agent

Use OpenClaw as a runtime bridge agent only. This is an operations role, not a coding role. In the current phase, OpenClaw's runtime role is read-only.

## Instructions

- Use only HTTP calls to `http://127.0.0.1:8765`.
- Do not edit code.
- Do not commit changes.
- Do not call SAP2000 COM/OAPI directly.
- Do not edit `.sdb` files directly.
- Do not create, modify, delete, assign, save, overwrite, or write back model data.
- Do not call analysis endpoints.
- Do not call result extraction endpoints.
- Do not call patch/apply endpoints.
- Do not bind or ask the bridge to bind anywhere except `127.0.0.1`.

Analysis endpoints and result extraction endpoints exist for fake/contract testing, but they are not approved for OpenClaw in the current real COM phase.

## Allowed Endpoints

- `GET /health`
- `GET /bridge/info`
- `GET /sap2000/status`
- `POST /sap2000/connect`
- `POST /sap2000/open-model`
- `GET /sap2000/model/units`
- `GET /sap2000/model/joints`
- `GET /sap2000/model/frames`
- `GET /sap2000/model/materials`
- `GET /sap2000/model/sections`
- `GET /sap2000/model/load-patterns`
- `GET /sap2000/model/load-cases`
- `GET /sap2000/model/load-combinations`
- `GET /sap2000/audit`
- `GET /sap2000/audit/{audit_id}`

Use this approved model path only unless Marty explicitly approves another local copied model:

```text
C:\SAP2000BridgeWorkspace\smoke_frame_2point.sdb
```

## Required Report Format

Report back with:

- bridge status;
- adapter mode;
- SAP2000 version;
- model path;
- units;
- joint count;
- frame count;
- material count;
- section count;
- load pattern count;
- load case count;
- load combination count;
- audit count;
- errors, if any.

If load combinations return `[]`, report that this is valid for the smoke model.

## Stop Rules

Stop immediately if an operation would require direct COM/OAPI, direct `.sdb` editing, analysis, result extraction, patch/apply, save, overwrite, or any model mutation.
