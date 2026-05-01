from pathlib import Path
import re
import sys

from bridge.config import Settings
from bridge.contracts.model import Sap2000TargetInfo


def inspect_sap2000_target(settings: Settings) -> Sap2000TargetInfo:
    install_dir = settings.sap2000_install_dir
    install_path = Path(install_dir) if install_dir else None

    sap2000_chm_path = str(install_path / "SAP2000.chm") if install_path else None
    native_api_dir = str(install_path / "NativeAPI") if install_path else None
    register_tool_path = str(install_path / "RegisterSAP2000.exe") if install_path else None

    install_dir_present = _exists_dir(install_dir)
    exe_present = _exists_file(settings.sap2000_exe_path)
    api_dll_present = _exists_file(settings.sap2000_api_dll_path)
    csi_api_dll_present = _exists_file(settings.csi_api_dll_path)
    oapi_chm_present = _exists_file(settings.sap2000_oapi_chm_path)
    sap2000_chm_present = _exists_file(sap2000_chm_path)
    native_api_dir_present = _exists_dir(native_api_dir)
    register_tool_present = _exists_file(register_tool_path)
    sap2000_helper_progid_registered = _registry_key_exists("SAP2000v1.Helper")
    csi_helper_progid_registered = _registry_key_exists("CSiAPIv1.Helper")
    sap_object_progid_registered = _registry_key_exists("CSI.SAP2000.API.SapObject")

    return Sap2000TargetInfo(
        configured_version=_version_from_install_dir(install_dir),
        install_dir=install_dir,
        exe_path=settings.sap2000_exe_path,
        api_dll_path=settings.sap2000_api_dll_path,
        csi_api_dll_path=settings.csi_api_dll_path,
        oapi_chm_path=settings.sap2000_oapi_chm_path,
        sap2000_chm_path=sap2000_chm_path,
        native_api_dir=native_api_dir,
        register_tool_path=register_tool_path,
        install_dir_present=install_dir_present,
        exe_present=exe_present,
        api_dll_present=api_dll_present,
        csi_api_dll_present=csi_api_dll_present,
        oapi_chm_present=oapi_chm_present,
        sap2000_chm_present=sap2000_chm_present,
        native_api_dir_present=native_api_dir_present,
        register_tool_present=register_tool_present,
        all_required_present=all(
            [
                install_dir_present,
                exe_present,
                api_dll_present,
                csi_api_dll_present,
                oapi_chm_present,
                sap2000_chm_present,
            ]
        ),
        sap2000_helper_progid_registered=sap2000_helper_progid_registered,
        csi_helper_progid_registered=csi_helper_progid_registered,
        sap_object_progid_registered=sap_object_progid_registered,
        com_registration_ready=sap2000_helper_progid_registered and sap_object_progid_registered,
    )


def _exists_file(path: str | None) -> bool:
    return bool(path) and Path(path).is_file()


def _exists_dir(path: str | None) -> bool:
    return bool(path) and Path(path).is_dir()


def _version_from_install_dir(path: str | None) -> str | None:
    if not path:
        return None
    match = re.search(r"SAP2000\s+(\d+)", path, flags=re.IGNORECASE)
    return f"SAP2000 {match.group(1)}" if match else None


def _registry_key_exists(progid: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid):
            return True
    except OSError:
        return False
