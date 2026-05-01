from pathlib import Path

from bridge.errors import BridgeError


class BackupService:
    def create_model_backup(self, model_path: str, reason: str | None = None) -> Path:
        """Disabled MVP stub. Future write-back must create a verified backup first."""
        raise BridgeError(
            http_status=501,
            bridge_code="BACKUPS_DISABLED",
            message="Model backup creation is disabled until the real write-back phase.",
            retryable=False,
        )

    def list_backups(self, model_path: str | None = None) -> list[Path]:
        """Disabled MVP stub. No backup inventory is maintained yet."""
        raise BridgeError(
            http_status=501,
            bridge_code="BACKUPS_DISABLED",
            message="Backup listing is disabled until the real write-back phase.",
            retryable=False,
        )

    def restore_backup(self, backup_path: str, target_model_path: str) -> None:
        """Disabled MVP stub. Restore would overwrite model data and is forbidden."""
        raise BridgeError(
            http_status=501,
            bridge_code="BACKUP_RESTORE_DISABLED",
            message="Backup restore is disabled in the read-only MVP.",
            retryable=False,
        )


backup_service = BackupService()
