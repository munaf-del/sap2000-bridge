from bridge.config import get_settings


def test_default_sap2000_27_paths_are_recorded() -> None:
    settings = get_settings()

    assert settings.csi_products_root == r"C:\Program Files\Computers and Structures"
    assert settings.sap2000_install_dir == r"C:\Program Files\Computers and Structures\SAP2000 27"
    assert settings.sap2000_exe_path.endswith(r"SAP2000 27\SAP2000.exe")
    assert settings.sap2000_api_dll_path.endswith(r"SAP2000 27\SAP2000v1.dll")
    assert settings.csi_api_dll_path.endswith(r"SAP2000 27\CSiAPIv1.dll")
    assert settings.sap2000_oapi_chm_path.endswith(r"SAP2000 27\CSI_OAPI_Documentation.chm")
