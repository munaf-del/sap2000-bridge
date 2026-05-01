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

    target = inspect_sap2000_target(
        Settings(
            sap2000_install_dir=str(install_dir),
            sap2000_exe_path=str(install_dir / "SAP2000.exe"),
            sap2000_api_dll_path=str(install_dir / "SAP2000v1.dll"),
            csi_api_dll_path=str(install_dir / "CSiAPIv1.dll"),
            sap2000_oapi_chm_path=str(install_dir / "CSI_OAPI_Documentation.chm"),
        )
    )

    assert target.configured_version == "SAP2000 27"
    assert target.all_required_present is True
    assert target.native_api_dir_present is True
    assert target.register_tool_present is True
    assert isinstance(target.com_registration_ready, bool)


def test_inspect_sap2000_target_fails_closed_for_missing_files(tmp_path) -> None:
    install_dir = tmp_path / "SAP2000 27"
    install_dir.mkdir()

    target = inspect_sap2000_target(
        Settings(
            sap2000_install_dir=str(install_dir),
            sap2000_exe_path=str(install_dir / "SAP2000.exe"),
            sap2000_api_dll_path=str(install_dir / "SAP2000v1.dll"),
            csi_api_dll_path=str(install_dir / "CSiAPIv1.dll"),
            sap2000_oapi_chm_path=str(install_dir / "CSI_OAPI_Documentation.chm"),
        )
    )

    assert target.configured_version == "SAP2000 27"
    assert target.install_dir_present is True
    assert target.all_required_present is False
    assert target.exe_present is False
    assert isinstance(target.sap2000_helper_progid_registered, bool)
