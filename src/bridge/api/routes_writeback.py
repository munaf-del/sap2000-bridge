from fastapi import APIRouter

from bridge.errors import BridgeError

router = APIRouter(prefix="/sap2000/patches")


def _writeback_disabled() -> None:
    raise BridgeError(
        http_status=501,
        bridge_code="WRITEBACK_DISABLED",
        message=(
            "Write-back is disabled in this read-only MVP. Future write-back requires preview, "
            "human approval, backup, validation, and audit."
        ),
        retryable=False,
    )


@router.post("/preview")
def preview_writeback() -> None:
    _writeback_disabled()


@router.post("/apply")
def apply_writeback() -> None:
    _writeback_disabled()
