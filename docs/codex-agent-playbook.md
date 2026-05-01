# Codex Agent Playbook

Codex can be used as a local coding agent or verification agent for the SAP2000 Local Bridge.

## Coding Agent

Codex may:

- edit code, tests, docs, examples, scripts, and prompts;
- run local tests;
- inspect local files;
- create checkpoint commits;
- push checkpoints to GitHub.

Codex must not:

- directly access SAP2000 COM/OAPI except through existing guarded bridge code;
- implement unapproved write-back;
- add create, modify, delete, assign, save, or overwrite behavior;
- remove safety comments or real COM guards;
- bind the bridge to `0.0.0.0`;
- push a checkpoint when tests fail.

## Verification Agent

Codex may:

- inspect the repository;
- check endpoint contracts;
- check fake mode remains default;
- check real COM remains guarded;
- check test isolation from COM environment variables;
- confirm no write-back behavior exists;
- confirm docs match the verified local state.

Codex must not silently change endpoint contracts or implement new unrequested features while acting as a verification agent.

## Checkpoint Workflow

Marty is the sole developer. GitHub is backup and revision history, not a slow PR gate.

After each prompt:

```powershell
python -m pytest -q
git status
git add -A
git commit -m "checkpoint-XX-description"
git push
```

If the prompt requires COM-env isolation, also run:

```powershell
$env:SAP2000_BRIDGE_ADAPTER_MODE = "comtypes"
$env:SAP2000_BRIDGE_ENABLE_REAL_COM = "1"
python -m pytest -q
```

Do not push a checkpoint until the test suite passes.

