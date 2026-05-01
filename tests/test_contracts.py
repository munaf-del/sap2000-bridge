from pydantic import ValidationError
import pytest

from bridge.contracts.common import ErrorEnvelope, UnitsInfo
from bridge.contracts.model import JointInfo


def test_units_contract_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        UnitsInfo(
            present="kN_m_C",
            database="N_mm_C",
            length="m",
            force="kN",
            moment="kN-m",
            unexpected=True,
        )


def test_joint_contract_optional_restraint() -> None:
    joint = JointInfo(name="J1", coord_system="Global", x=0, y=1, z=2, units_ref="m")

    assert joint.restraint is None


def test_error_envelope_contract() -> None:
    envelope = ErrorEnvelope(
        error={
            "http_status": 409,
            "bridge_code": "NO_MODEL_OPEN",
            "message": "No model open.",
            "sap_ret": None,
            "sap_context": None,
            "retryable": False,
            "correlation_id": "abc",
        }
    )

    assert envelope.error.bridge_code == "NO_MODEL_OPEN"
