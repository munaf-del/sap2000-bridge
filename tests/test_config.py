from bridge.config import Settings, get_settings


def test_default_sap2000_27_paths_are_recorded() -> None:
    settings = get_settings()

    assert settings.csi_products_root == r"C:\Program Files\Computers and Structures"
    assert settings.sap2000_install_dir == r"C:\Program Files\Computers and Structures\SAP2000 27"
    assert settings.sap2000_exe_path.endswith(r"SAP2000 27\SAP2000.exe")
    assert settings.sap2000_api_dll_path.endswith(r"SAP2000 27\SAP2000v1.dll")
    assert settings.csi_api_dll_path.endswith(r"SAP2000 27\CSiAPIv1.dll")
    assert settings.sap2000_oapi_chm_path.endswith(r"SAP2000 27\CSI_OAPI_Documentation.chm")


def test_manual_real_com_environment_aliases(monkeypatch) -> None:
    monkeypatch.setenv("SAP2000_BRIDGE_ENABLE_REAL_COM", "1")
    monkeypatch.setenv("SAP2000_EXE_PATH", r"C:\custom\SAP2000.exe")
    monkeypatch.setenv("SAP2000_MODEL_PATH", r"C:\models\manual.sdb")
    monkeypatch.setenv("SAP2000_WORKSPACE", r"C:\sap2000-smoke")

    settings = Settings()

    assert settings.enable_real_com is True
    assert settings.sap2000_exe_path == r"C:\custom\SAP2000.exe"
    assert settings.sap2000_model_path == r"C:\models\manual.sdb"
    assert settings.sap2000_workspace == r"C:\sap2000-smoke"
