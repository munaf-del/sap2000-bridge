from bridge.config import Settings
from bridge.services.install_validator import inspect_sap2000_target


def test_inspect_sap2000_target_detects_required_files(tmp_path) -> None:
    install_dir = tmp_path / "SAP2000 27"
    install_dir.mkdir()
    for name in [
        "SAP2000.exe",
        "SAP2000v1.dll",
        "CSiAPIv1.dll",
        "CSI_OAPI_Documentation.chm",
        "SAP2000.chm",
        "RegisterSAP2000.exe",
    ]:
        (install_dir / name).write_text("", encoding="utf-8")
    (install_dir / "NativeAPI").mkdir()

    inspection = inspect_sap2000_target(
        Settings(
            sap2000_install_dir=str(install_dir),
            sap2000_exe_path=str(install_dir / "SAP2000.exe"),
            sap2000_api_dll_path=str(install_dir / "SAP2000v1.dll"),
            csi_api_dll_path=str(install_dir / "CSiAPIv1.dll"),
            sap2000_oapi_chm_path=str(install_dir / "CSI_OAPI_Documentation.chm"),
        )
    )

    assert inspection.target.configured_version == "SAP2000 27"
    assert inspection.validation.all_required_present is True
    assert inspection.validation.native_api_present is True
    assert inspection.validation.register_sap2000_present is True
    assert isinstance(inspection.validation.com_registration_ready, bool)


def test_inspect_sap2000_target_fails_closed_for_missing_files(tmp_path) -> None:
    install_dir = tmp_path / "SAP2000 27"
    install_dir.mkdir()

    inspection = inspect_sap2000_target(
        Settings(
            sap2000_install_dir=str(install_dir),
            sap2000_exe_path=str(install_dir / "SAP2000.exe"),
            sap2000_api_dll_path=str(install_dir / "SAP2000v1.dll"),
            csi_api_dll_path=str(install_dir / "CSiAPIv1.dll"),
            sap2000_oapi_chm_path=str(install_dir / "CSI_OAPI_Documentation.chm"),
        )
    )

    assert inspection.target.configured_version == "SAP2000 27"
    assert inspection.validation.all_required_present is False
    assert inspection.validation.sap2000_exe_present is False
    assert isinstance(inspection.validation.helper_progids["SAP2000v1.Helper"], bool)
    assert inspection.validation.warnings
