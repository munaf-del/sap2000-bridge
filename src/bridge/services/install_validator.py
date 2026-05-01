from pathlib import Path
import re
import sys
from typing import NamedTuple

from bridge.config import Settings
from bridge.contracts.model import InstallValidation, Sap2000TargetInfo


class Sap2000InstallInspection(NamedTuple):
    target: Sap2000TargetInfo
    validation: InstallValidation


def inspect_sap2000_target(settings: Settings) -> Sap2000InstallInspection:
    install_dir = settings.sap2000_install_dir
    install_path = Path(install_dir) if install_dir else None

    sap2000_chm_path = str(install_path / "SAP2000.chm") if install_path else None
    native_api_path = str(install_path / "NativeAPI") if install_path else None
    register_sap2000_path = str(install_path / "RegisterSAP2000.exe") if install_path else None

    configured_version = _version_from_install_dir(install_dir)
    sap2000_exe_present = _exists_file(settings.sap2000_exe_path)
    sap2000v1_dll_present = _exists_file(settings.sap2000_api_dll_path)
    csiapiv1_dll_present = _exists_file(settings.csi_api_dll_path)
    csi_oapi_documentation_present = _exists_file(settings.sap2000_oapi_chm_path)
    sap2000_chm_present = _exists_file(sap2000_chm_path)
    native_api_present = _exists_dir(native_api_path)
    register_sap2000_present = _exists_file(register_sap2000_path)
    sap2000_helper_progid_registered = _registry_key_exists("SAP2000v1.Helper")
    csi_helper_progid_registered = _registry_key_exists("CSiAPIv1.Helper")
    sap_object_progid_registered = _registry_key_exists("CSI.SAP2000.API.SapObject")
    all_required_present = all(
        [
            _exists_dir(install_dir),
            sap2000_exe_present,
            sap2000v1_dll_present,
            csiapiv1_dll_present,
            csi_oapi_documentation_present,
            sap2000_chm_present,
        ]
    )
    com_registration_ready = sap2000_helper_progid_registered and sap_object_progid_registered
    warnings = _build_warnings(
        settings=settings,
        all_required_present=all_required_present,
        native_api_present=native_api_present,
        register_sap2000_present=register_sap2000_present,
        com_registration_ready=com_registration_ready,
    )

    return Sap2000InstallInspection(
        target=Sap2000TargetInfo(
            configured_version=configured_version,
            configured_root=settings.csi_products_root,
            install_dir=install_dir,
            exe_path=settings.sap2000_exe_path,
            sap2000v1_dll_path=settings.sap2000_api_dll_path,
            csiapiv1_dll_path=settings.csi_api_dll_path,
            csi_oapi_documentation_path=settings.sap2000_oapi_chm_path,
            sap2000_chm_path=sap2000_chm_path,
            native_api_path=native_api_path,
            register_sap2000_path=register_sap2000_path,
        ),
        validation=InstallValidation(
            configured_version=configured_version,
            configured_root=settings.csi_products_root,
            sap2000_exe_present=sap2000_exe_present,
            sap2000v1_dll_present=sap2000v1_dll_present,
            csiapiv1_dll_present=csiapiv1_dll_present,
            csi_oapi_documentation_present=csi_oapi_documentation_present,
            sap2000_chm_present=sap2000_chm_present,
            native_api_present=native_api_present,
            register_sap2000_present=register_sap2000_present,
            all_required_present=all_required_present,
            com_registration_ready=com_registration_ready,
            helper_progids={
                "SAP2000v1.Helper": sap2000_helper_progid_registered,
                "CSiAPIv1.Helper": csi_helper_progid_registered,
            },
            sap_object_progid={"CSI.SAP2000.API.SapObject": sap_object_progid_registered},
            warnings=warnings,
        ),
    )


def inspect_sap2000_target_info(settings: Settings) -> Sap2000TargetInfo:
    return inspect_sap2000_target(settings).target


def inspect_sap2000_install_validation(settings: Settings) -> InstallValidation:
    return inspect_sap2000_target(settings).validation


def _build_warnings(
    settings: Settings,
    all_required_present: bool,
    native_api_present: bool,
    register_sap2000_present: bool,
    com_registration_ready: bool,
) -> list[str]:
    warnings: list[str] = []
    if not settings.sap2000_install_dir:
        warnings.append("SAP2000 install directory is not configured.")
    if not all_required_present:
        warnings.append("One or more required SAP2000 bridge artefacts are missing.")
    if not native_api_present:
        warnings.append("NativeAPI directory was not found; real adapter verification may be incomplete.")
    if not register_sap2000_present:
        warnings.append("RegisterSAP2000.exe was not found; COM registration repair may require manual steps.")
    if sys.platform != "win32":
        warnings.append("COM registration was not checked because this is not Windows.")
    elif not com_registration_ready:
        warnings.append("Required SAP2000 COM ProgIDs are not fully registered.")
    return warnings


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
