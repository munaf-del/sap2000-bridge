# Agent Operating Policy

This policy is for OpenClaw/Codex-style agents working with the SAP2000 Local Bridge. Agents may help code or operate the bridge, but they must not bypass it.

Marty is the sole developer. GitHub is used as fast backup and revision history, not as a slow PR/review gate.

## Global Rules

- Agents must use approved local bridge endpoints only when operating SAP2000.
- Agents must not directly access SAP2000 COM/OAPI.
- Agents must not directly edit `.sdb` files.
- Agents must not create, modify, assign, delete, save, overwrite, or write back model data.
- Agents must not call disabled patch/apply endpoints in the MVP.
- Agents must preserve safety comments and verification comments.
- Agents must keep units attached to model/result interpretation.

## Human Approval Required

Human approval is required before:

- launching SAP2000;
- opening a model;
- running analysis;
- uploading or exporting results;
- switching from fake mode to comtypes mode.

## Coding Agent

Allowed:

- create code;
- run tests;
- refactor;
- update docs;
- checkpoint commits.

Forbidden:

- direct SAP2000 COM access;
- real model modification;
- writeback;
- deleting safety comments;
- bypassing tests.

## Verification Agent

Allowed:

- inspect code;
- compare against contracts;
- check safety;
- confirm no writeback.

Forbidden:

- implement new unrequested features;
- remove guardrails;
- silently change endpoint contracts.

## Runtime Bridge Agent

Allowed endpoints:

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
- `GET /sap2000/audit`
- `GET /sap2000/audit/{audit_id}`

Forbidden:

- direct COM/OAPI;
- direct `.sdb` editing;
- save/overwrite;
- writeback endpoints;
- patch/apply;
- create/modify/delete/assign;
- shell commands that launch SAP2000 unless explicitly approved;
- interpreting results without units.
