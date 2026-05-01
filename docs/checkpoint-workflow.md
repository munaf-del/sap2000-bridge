# Checkpoint Workflow

Marty is the sole developer for this repository. GitHub is backup and revision history, so the workflow is fast checkpoint-based work rather than a slow PR gate.

After each prompt:

1. Run tests:

```powershell
pytest -q
```

2. Review status:

```powershell
git status
```

3. Stage the completed prompt work:

```powershell
git add -A
```

4. Commit with the requested checkpoint name:

```powershell
git commit -m "checkpoint-XX-description"
```

5. Push:

```powershell
git push
```

If tests fail, fix the issue first. Do not push a checkpoint until the test suite passes.
