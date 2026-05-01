from pathlib import Path


def backup_model_before_writeback(model_path: str) -> Path:
    """Disabled MVP stub.

    Future write-back must create a verified backup before any model mutation.
    """
    raise RuntimeError("Write-back backups are disabled in the read-only MVP.")
