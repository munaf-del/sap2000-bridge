from typing import NoReturn


def preview_writeback() -> NoReturn:
    """Disabled MVP stub.

    Write-back requires preview, explicit human approval, backup, validation,
    and audit records before any endpoint can be enabled.
    """
    raise RuntimeError("Write-back is disabled in this read-only MVP.")


def apply_writeback() -> NoReturn:
    """Disabled MVP stub. No model create/modify/delete/assign/save is allowed."""
    raise RuntimeError("Write-back is disabled in this read-only MVP.")
