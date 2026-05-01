# Local Agent Operations

This pack explains how Marty can use Codex and OpenClaw locally with the SAP2000 Local Bridge before EngPlatform integration.

The bridge stays local-only:

- base URL: `http://127.0.0.1:8765`
- host: `127.0.0.1`
- port: `8765`
- do not bind to `0.0.0.0`
- real COM mode must run in native Windows PowerShell, not Docker, WSL, or Ubuntu

## Operating Model

Marty is the single human approver. GitHub is fast checkpoint history and backup for Marty, not a slow PR gate.

Codex can act as:

- Coding Agent: edit code, docs, tests, and checkpoints.
- Verification Agent: inspect the repository, compare behavior against contracts, and report safety risks.

OpenClaw should act as:

- Runtime Bridge Agent: call approved local HTTP endpoints only.

Agents must not bypass the bridge. They must not directly access SAP2000 COM/OAPI or directly edit `.sdb` files.

## Current Verified State

- SAP2000 version: `27.1.0`
- bridge: `http://127.0.0.1:8765`
- adapter: `comtypes` for manual smoke, `fake` by default
- smoke model: `C:\SAP2000BridgeWorkspace\smoke_frame_2point.sdb`
- units: `kN_m_C`
- joints: `2`
- frames: `1`
- materials: `3`
- sections: `1`
- load patterns: `1`
- load cases: `2`
- load combinations: `0`

Real analysis is not implemented. Real result extraction is not implemented. Write-back is disabled.

## Allowed Runtime Operations

Runtime agents may call only approved bridge endpoints for:

- health, bridge info, and status;
- attach to already-running SAP2000;
- open the approved smoke model after human approval;
- read units;
- read joints, frames, materials, sections, load patterns, load cases, and load combinations;
- read audit records.

## Forbidden Operations

Agents must not:

- call direct SAP2000 COM/OAPI;
- directly edit `.sdb` files;
- create, modify, delete, assign, save, overwrite, or write back model data;
- call patch/apply endpoints;
- run real analysis;
- request real result extraction;
- bind the bridge to network interfaces other than loopback;
- interpret model data without units;
- continue after a safety or contract error without reporting it.

## Stop Rules

Stop and report to Marty if:

- the bridge is not on `127.0.0.1:8765`;
- `/bridge/info` does not match the expected adapter mode for the task;
- real COM mode is requested outside native Windows PowerShell;
- SAP2000 is not already running for an attach-only task;
- the model path differs from the approved smoke model;
- any endpoint returns a standard error envelope;
- a task requires analysis, results, patch/apply, save, or write-back.

## Local Scripts

- `scripts/start_bridge_fake.ps1`: starts the bridge in fake mode.
- `scripts/start_bridge_comtypes.ps1`: starts the bridge in guarded real COM mode.
- `scripts/stop_bridge.ps1`: stops only the process listening on `127.0.0.1:8765`.
- `scripts/agent_readonly_smoke.ps1`: runs the approved read-only local smoke sequence.
- `examples/agent_readonly_smoke.py`: Python equivalent using the restricted agent client.

