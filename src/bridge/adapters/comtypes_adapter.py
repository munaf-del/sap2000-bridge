from collections.abc import Iterable, Sequence
from contextlib import contextmanager
import logging
from pathlib import Path, PureWindowsPath
import shutil
import sys
import time
from typing import Any

from bridge.adapters.base import SapAdapter
from bridge.config import Settings, get_settings
from bridge.contracts.common import UnitsInfo
from bridge.contracts.model import (
    FrameListResponse,
    JointInfo,
    JointListResponse,
    JointRestraint,
    LoadCaseListResponse,
    LoadCombinationListResponse,
    LoadPatternListResponse,
    MaterialListResponse,
    OpenModelResponse,
    SapSessionInfo,
    SapStatusResponse,
    SectionListResponse,
)
from bridge.contracts.results import AnalysisJobStatus, FrameForceSetResponse, JointReactionSet, ModalPeriodSetResponse
from bridge.errors import BridgeError, NoModelOpenError, NotConnectedError

if sys.platform == "win32":  # pragma: no cover - comtypes is optional and not used in automated tests.
    try:
        import comtypes as comtypes_module
        import comtypes.client as comtypes_client
    except ImportError:
        comtypes_module = None
        comtypes_client = None
else:  # pragma: no cover - keeps non-Windows imports clean.
    comtypes_module = None
    comtypes_client = None


VERIFY_CHM = "VERIFY AGAINST INSTALLED SAP2000 API CHM"
VERIFY_TLB = "VERIFY AGAINST SAP2000v1.tlb"
VERIFY_COMTYPES = "VERIFY comtypes tuple/byref behaviour on target machine"
VERIFY_ALL = f"{VERIFY_CHM}; {VERIFY_TLB}; {VERIFY_COMTYPES}"

KNOWN_UNIT_LABELS: dict[int, str] = {
    # TODO: finalize SAP2000 27 eUnits enum mapping from CSI_OAPI_Documentation.chm and SAP2000v1.tlb.
    # These common values are deliberately conservative; unknown values are returned raw.
    6: "kN_m_C",
}

KNOWN_UNIT_COMPONENTS: dict[int, dict[str, str]] = {
    # SAP2000 27 smoke verification observed raw enum 6 as kN_m_C.
    6: {"length": "m", "force": "kN", "moment": "kN-m", "temperature": "C"},
}

logger = logging.getLogger(__name__)


def check_ret(ret: int | None, operation: str, sap_context: str | None = None) -> None:
    """Normalize every SAP2000 return code before callers see it."""
    if ret not in (None, 0):
        context = sap_context or operation
        raise BridgeError(
            http_status=502,
            bridge_code="SAP2000_RETURN_CODE",
            message=f"SAP2000 API call failed during {operation}.",
            sap_ret=ret,
            sap_context=context,
            retryable=False,
        )


class ComtypesSapAdapter(SapAdapter):
    """Guarded SAP2000 27 COM smoke adapter.

    Only the narrow manual smoke path is implemented here: helper creation,
    attach, launch, version, open model, units, and joints. All broader model,
    analysis, result, and write-back operations remain disabled placeholders.
    """

    adapter_mode = "comtypes"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self.helper_progid = "SAP2000v1.Helper"
        self.csi_helper_progid = "CSiAPIv1.Helper"
        self.sap_object_progid = "CSI.SAP2000.API.SapObject"
        self.helper_progid_used: str | None = None
        self.install_dir = self._settings.sap2000_install_dir
        self.exe_path = self._settings.sap2000_exe_path
        self.api_dll_path = self._settings.sap2000_api_dll_path
        self.csi_api_dll_path = self._settings.csi_api_dll_path
        self.oapi_chm_path = self._settings.sap2000_oapi_chm_path
        self._ensure_real_com_enabled()
        self._helper = None
        self._sap_object = None
        self._sap_model = None
        self._connected = False
        self._launched_by_bridge = False
        self._model_path: str | None = None
        self._version_label: str | None = None
        self._version_number: str | None = None
        self._units: UnitsInfo | None = None

    def create_helper(self) -> object:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        if self._helper is None:
            last_error: Exception | None = None
            for helper_progid in (self.helper_progid, self.csi_helper_progid):
                try:
                    with self._com_scope():
                        self._helper = comtypes_client.CreateObject(helper_progid)  # type: ignore[union-attr]
                    self.helper_progid_used = helper_progid
                    logger.info("SAP2000 COM helper created with ProgID %s", helper_progid)
                    break
                except Exception as exc:
                    last_error = exc
                    logger.debug("SAP2000 COM helper ProgID failed: %s", helper_progid, exc_info=True)
            if self._helper is None:
                raise BridgeError(
                    http_status=503,
                    bridge_code="ADAPTER_UNAVAILABLE",
                    message="Could not create a SAP2000 COM helper with SAP2000v1.Helper or CSiAPIv1.Helper.",
                    sap_context="comtypes.client.CreateObject(SAP2000v1.Helper|CSiAPIv1.Helper)",
                    retryable=True,
                ) from last_error
        return self._helper

    def attach_to_running(self) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        with self._com_scope():
            helper = self.create_helper()
            try:
                self._sap_object = helper.GetObject(self.sap_object_progid)
            except Exception as exc:
                raise BridgeError(
                    http_status=503,
                    bridge_code="SAP2000_NOT_RUNNING",
                    message="Could not attach to a running SAP2000 instance.",
                    sap_context="Helper.GetObject",
                    retryable=True,
                ) from exc
            self._bind_sap_model()
            self._connected = True
            self._launched_by_bridge = False
            return self.get_version()

    def connect(self, attach_to_running: bool = True, exe_path: str | None = None) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        if attach_to_running:
            return self.attach_to_running()
        raise BridgeError(
            http_status=409,
            bridge_code="ATTACH_ONLY_REQUIRED",
            message="Real COM connect does not launch SAP2000. Use /sap2000/launch for launch behavior.",
            retryable=False,
        )

    def launch(
        self,
        exe_path: str | None = None,
        visible: bool = True,
        startup_delay_s: float = 3.0,
    ) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        selected_exe = exe_path or self.exe_path
        if not selected_exe or not Path(selected_exe).is_file():
            raise BridgeError(
                http_status=503,
                bridge_code="ADAPTER_UNAVAILABLE",
                message=f"SAP2000 executable was not found: {selected_exe}",
                retryable=False,
            )

        with self._com_scope():
            helper = self.create_helper()
            try:
                self._sap_object = helper.CreateObject(selected_exe)
            except Exception as exc:
                raise BridgeError(
                    http_status=502,
                    bridge_code="SAP2000_COM_ERROR",
                    message="SAP2000 helper could not create a SapObject for launch.",
                    sap_context="Helper.CreateObject",
                    retryable=False,
                ) from exc

            # VERIFY AGAINST INSTALLED SAP2000 API CHM
            # VERIFY AGAINST SAP2000v1.tlb
            # VERIFY comtypes tuple/byref behaviour on target machine
            ret = self._call(
                lambda: self._sap_object.ApplicationStart(),
                operation="SapObject.ApplicationStart",
                sap_context="cOAPI.ApplicationStart",
            )
            self._check_ret_result(ret, "SapObject.ApplicationStart", "cOAPI.ApplicationStart")
            if startup_delay_s > 0:
                time.sleep(startup_delay_s)
            self._bind_sap_model(retries=10, delay_s=0.5)
            self._connected = True
            self._launched_by_bridge = True
            return self.get_version()

    def get_version(self) -> SapSessionInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        self._require_connected_object()
        result = self._call(
            lambda: self._sap_model.GetVersion(),
            operation="SapModel.GetVersion",
            sap_context="cSapModel.GetVersion",
        )
        version_label, version_number = self._parse_get_version_result(result)
        self._version_label = version_label
        self._version_number = version_number
        return SapSessionInfo(
            connected=True,
            launched_by_bridge=self._launched_by_bridge,
            version_label=version_label,
            version_number=version_number,
            adapter_mode=self.adapter_mode,
        )

    def status(self) -> SapStatusResponse:
        return SapStatusResponse(
            connected=self._connected,
            launched_by_bridge=self._launched_by_bridge,
            model_open=self._model_path is not None,
            model_path=self._model_path,
            model_name=self._model_name,
            version_label=self._version_label,
            version_number=self._version_number,
            adapter_mode=self.adapter_mode,
            correlation_id="",
        )

    def open_model(self, path: str, copy_to_workspace: bool = False) -> OpenModelResponse:
        self._require_connected_object()
        model_path = self._prepare_model_path(path=path, copy_to_workspace=copy_to_workspace)
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        ret = self._call(
            lambda: self._sap_model.File.OpenFile(str(model_path)),
            operation="File.OpenFile",
            sap_context="cFile.OpenFile",
        )
        self._check_ret_result(ret, "File.OpenFile", "cFile.OpenFile")
        self._model_path = str(model_path)
        self.get_version()
        self._units = self.get_units()
        return OpenModelResponse(
            model_open=True,
            model_path=str(model_path),
            model_name=self._model_name or model_path.name,
            version_label=self._version_label or "",
            version_number=self._version_number or "",
            adapter_mode=self.adapter_mode,
            units=self._units,
        )

    def get_units(self) -> UnitsInfo:
        self._require_model()
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        present_result = self._call(
            lambda: self._sap_model.GetPresentUnits(),
            operation="SapModel.GetPresentUnits",
            sap_context="cSapModel.GetPresentUnits",
        )
        database_result = self._call(
            lambda: self._sap_model.GetDatabaseUnits(),
            operation="SapModel.GetDatabaseUnits",
            sap_context="cSapModel.GetDatabaseUnits",
        )
        present_raw = self._single_value_from_result(present_result, "SapModel.GetPresentUnits")
        database_raw = self._single_value_from_result(database_result, "SapModel.GetDatabaseUnits")
        self._units = self._units_from_raw(present_raw=present_raw, database_raw=database_raw)
        return self._units

    def list_joints(self, csys: str = "Global", include_restraints: bool = False) -> JointListResponse:
        self._require_model()
        units = self.get_units()
        all_points = self._try_get_all_points(csys=csys)
        if all_points is not None:
            joints = [
                JointInfo(
                    name=name,
                    coord_system=csys,
                    x=x,
                    y=y,
                    z=z,
                    units_ref=units.length,
                    restraint=None,
                )
                for name, x, y, z in all_points
            ]
            return JointListResponse(
                model_path=self._model_path or "",
                model_name=self._model_name or "",
                version_label=self._version_label or "",
                version_number=self._version_number or "",
                adapter_mode=self.adapter_mode,
                units=units,
                joints=joints,
            )

        names = self._get_point_names()
        joints = [
            self._joint_from_name(name=name, csys=csys, include_restraints=include_restraints, units=units)
            for name in names
        ]
        return JointListResponse(
            model_path=self._model_path or "",
            model_name=self._model_name or "",
            version_label=self._version_label or "",
            version_number=self._version_number or "",
            adapter_mode=self.adapter_mode,
            units=units,
            joints=joints,
        )

    def list_frames(self, csys: str = "Global") -> FrameListResponse:
        # Likely call family: FrameObj.GetAllFrames or fallback FrameObj.GetNameList +
        # FrameObj.GetPoints + FrameObj.GetSection.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_frames")

    def list_materials(self) -> MaterialListResponse:
        # Likely call family: PropMaterial.GetNameList / GetMaterial.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_materials")

    def list_sections(self) -> SectionListResponse:
        # Likely call family: PropFrame.GetNameList.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_sections")

    def list_load_patterns(self) -> LoadPatternListResponse:
        # Likely call family: LoadPatterns.GetNameList / GetLoadType.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_patterns")

    def list_load_cases(self) -> LoadCaseListResponse:
        # Likely call family: LoadCases.GetNameList / GetTypeOAPI.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_cases")

    def list_load_combinations(self) -> LoadCombinationListResponse:
        # Likely call family: RespCombo.GetNameList / GetCaseList / GetTypeCombo.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("list_load_combinations")

    def run_analysis(
        self,
        save_before_run: bool = False,
        case_names: list[str] | None = None,
    ) -> AnalysisJobStatus:
        # Likely call family: Analyze.RunAnalysis and, if available, Analyze.GetCaseStatus.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("run_analysis")

    def extract_joint_reactions(
        self,
        point_name: str,
        case_names: list[str],
        combo_names: list[str],
    ) -> JointReactionSet:
        # Likely setup calls: Results.Setup.DeselectAllCasesAndCombosForOutput,
        # Results.Setup.SetCaseSelectedForOutput, Results.Setup.SetComboSelectedForOutput.
        # Likely result call: Results.JointReact.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("extract_joint_reactions")

    def extract_frame_forces(
        self,
        frame_name: str | None,
        case_names: list[str],
        combo_names: list[str],
    ) -> FrameForceSetResponse:
        # Likely setup calls: Results.Setup.DeselectAllCasesAndCombosForOutput,
        # Results.Setup.SetCaseSelectedForOutput, Results.Setup.SetComboSelectedForOutput.
        # Likely result call: Results.FrameForce.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("extract_frame_forces")

    def extract_modal_periods(self, case_names: list[str]) -> ModalPeriodSetResponse:
        # Likely setup calls: Results.Setup.DeselectAllCasesAndCombosForOutput,
        # Results.Setup.SetCaseSelectedForOutput.
        # Likely result call: Results.ModalPeriod.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        raise self._placeholder("extract_modal_periods")

    @property
    def _model_name(self) -> str | None:
        return PureWindowsPath(self._model_path).name if self._model_path else None

    @contextmanager
    def _com_scope(self):
        initialized = False
        if comtypes_module is not None:
            try:
                comtypes_module.CoInitialize()
                initialized = True
            except Exception:
                logger.debug("COM initialization failed or was already incompatible on this thread.", exc_info=True)
        try:
            yield
        finally:
            if initialized:
                try:
                    comtypes_module.CoUninitialize()
                except Exception:
                    logger.debug("COM uninitialization failed.", exc_info=True)

    def _ensure_real_com_enabled(self) -> None:
        if sys.platform != "win32":
            raise BridgeError(
                http_status=503,
                bridge_code="ADAPTER_UNAVAILABLE",
                message="ComtypesSapAdapter is unavailable because real SAP2000 COM requires Windows.",
                retryable=False,
            )
        if comtypes_client is None:
            raise BridgeError(
                http_status=503,
                bridge_code="ADAPTER_UNAVAILABLE",
                message=(
                    "ComtypesSapAdapter is unavailable because comtypes is not installed. "
                    "Install the Windows-only sap2000 optional extra for manual real-COM smoke checks."
                ),
                retryable=True,
            )
        if not self._settings.enable_real_com:
            raise BridgeError(
                http_status=503,
                bridge_code="REAL_COM_DISABLED",
                message=(
                    "Real SAP2000 COM execution is disabled. Set SAP2000_BRIDGE_ENABLE_REAL_COM=1 "
                    "for manual smoke verification."
                ),
                retryable=False,
            )

    def _bind_sap_model(self, retries: int = 1, delay_s: float = 0.0) -> None:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                self._sap_model = self._sap_object.SapModel
                return
            except Exception as exc:
                last_error = exc
                if attempt + 1 < retries and delay_s > 0:
                    time.sleep(delay_s)
        raise BridgeError(
            http_status=502,
            bridge_code="SAP2000_COM_ERROR",
            message="SAP2000 SapModel object was not available after COM connection.",
            sap_context="cOAPI.SapModel",
            retryable=True,
        ) from last_error

    def _prepare_model_path(self, path: str, copy_to_workspace: bool) -> Path:
        model_path = Path(path)
        if model_path.suffix.lower() != ".sdb":
            raise BridgeError(
                http_status=400,
                bridge_code="INVALID_MODEL_FILE",
                message=f"Model path must point to a .sdb file: {path}",
                retryable=False,
            )
        try:
            source_exists = model_path.is_file()
        except PermissionError as exc:
            raise BridgeError(
                http_status=423,
                bridge_code="MODEL_FILE_LOCKED",
                message=f"Model file could not be inspected because it is locked or inaccessible: {path}",
                retryable=True,
            ) from exc
        if not source_exists:
            raise BridgeError(
                http_status=404,
                bridge_code="MODEL_FILE_NOT_FOUND",
                message=f"Model file was not found: {path}",
                retryable=False,
            )
        if not copy_to_workspace:
            return model_path

        if not self._settings.sap2000_workspace:
            raise BridgeError(
                http_status=400,
                bridge_code="WORKSPACE_REQUIRED",
                message="copy_to_workspace=true requires SAP2000_WORKSPACE or SAP2000_BRIDGE_SAP2000_WORKSPACE.",
                retryable=False,
            )
        workspace = Path(self._settings.sap2000_workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        copied_path = self._unique_workspace_path(workspace=workspace, source_path=model_path)
        try:
            if not _same_file(model_path, copied_path):
                shutil.copy2(model_path, copied_path)
        except PermissionError as exc:
            raise BridgeError(
                http_status=423,
                bridge_code="MODEL_FILE_LOCKED",
                message=f"Model file could not be copied because it is locked or inaccessible: {path}",
                retryable=True,
            ) from exc
        return copied_path

    @staticmethod
    def _unique_workspace_path(workspace: Path, source_path: Path) -> Path:
        candidate = workspace / source_path.name
        if _same_file(source_path, candidate):
            return candidate
        if not candidate.exists():
            return candidate
        stem = source_path.stem
        suffix = source_path.suffix
        for index in range(1, 1000):
            candidate = workspace / f"{stem}-{index}{suffix}"
            if not candidate.exists():
                return candidate
        raise BridgeError(
            http_status=409,
            bridge_code="MODEL_WORKSPACE_CONFLICT",
            message=f"Could not choose a unique workspace filename for {source_path.name}.",
            retryable=False,
        )

    def _try_get_all_points(self, csys: str) -> list[tuple[str, float, float, float]] | None:
        # Preferred PointObj.GetAllPoints. SAP2000 27 may not expose this on all installations.
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        try:
            result = self._call(
                lambda: self._sap_model.PointObj.GetAllPoints(0, [], [], [], [], csys),
                operation="PointObj.GetAllPoints",
                sap_context="cPointObj.GetAllPoints",
            )
        except BridgeError as exc:
            if exc.bridge_code == "SAP2000_COM_ERROR":
                logger.debug("PointObj.GetAllPoints unavailable; falling back to GetNameList.", exc_info=True)
                return None
            raise
        try:
            return self._parse_get_all_points_result(result)
        except BridgeError as exc:
            if exc.bridge_code == "SAP2000_COM_SIGNATURE_UNVERIFIED":
                logger.debug("PointObj.GetAllPoints signature uncertain; falling back to GetNameList.", exc_info=True)
                return None
            raise

    def _get_point_names(self) -> list[str]:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        try:
            result = self._call(
                lambda: self._sap_model.PointObj.GetNameList(0, []),
                operation="PointObj.GetNameList",
                sap_context="cPointObj.GetNameList",
            )
        except BridgeError:
            result = self._call(
                lambda: self._sap_model.PointObj.GetNameList(),
                operation="PointObj.GetNameList",
                sap_context="cPointObj.GetNameList",
            )
        return self._parse_get_name_list_result(result)

    def _joint_from_name(
        self,
        name: str,
        csys: str,
        include_restraints: bool,
        units: UnitsInfo,
    ) -> JointInfo:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        point_name = str(name)
        coord_result = self._call(
            lambda: self._sap_model.PointObj.GetCoordCartesian(point_name, 0.0, 0.0, 0.0, csys),
            operation="PointObj.GetCoordCartesian",
            sap_context=f"cPointObj.GetCoordCartesian({point_name})",
        )
        x, y, z = self._parse_get_coord_cartesian_result(coord_result, point_name)
        restraint = self._get_restraint(point_name) if include_restraints else None
        return JointInfo(
            name=point_name,
            coord_system=csys,
            x=x,
            y=y,
            z=z,
            units_ref=units.length,
            restraint=restraint,
        )

    def _get_restraint(self, name: str) -> JointRestraint | None:
        # VERIFY AGAINST INSTALLED SAP2000 API CHM
        # VERIFY AGAINST SAP2000v1.tlb
        # VERIFY comtypes tuple/byref behaviour on target machine
        result = self._call(
            lambda: self._sap_model.PointObj.GetRestraint(name),
            operation="PointObj.GetRestraint",
            sap_context=f"cPointObj.GetRestraint({name})",
        )
        values = self._values_from_result(result, "PointObj.GetRestraint", f"cPointObj.GetRestraint({name})")
        flags = self._first_bool_sequence(values)
        if flags is None or len(flags) < 6:
            raise self._signature_error("PointObj.GetRestraint")
        return JointRestraint(
            u1=flags[0],
            u2=flags[1],
            u3=flags[2],
            r1=flags[3],
            r2=flags[4],
            r3=flags[5],
        )

    @staticmethod
    def _call(func, operation: str, sap_context: str):
        initialized = False
        try:
            if comtypes_module is not None:
                try:
                    comtypes_module.CoInitialize()
                    initialized = True
                except Exception:
                    logger.debug("COM initialization failed or was already incompatible on this thread.", exc_info=True)
            return func()
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError(
                http_status=502,
                bridge_code="SAP2000_COM_ERROR",
                message=f"SAP2000 COM call failed during {operation}.",
                sap_context=sap_context,
                retryable=False,
            ) from exc
        finally:
            if initialized:
                try:
                    comtypes_module.CoUninitialize()
                except Exception:
                    logger.debug("COM uninitialization failed.", exc_info=True)

    def _check_ret_result(self, result, operation: str, sap_context: str) -> None:
        ret = self._extract_ret_code(result)
        if ret is None and self._is_ret(result):
            ret = int(result)
        check_ret(ret, operation, sap_context)

    def _single_value_from_result(self, result, operation: str):
        if not self._is_sequence(result):
            return result
        values = self._payload_without_ret(result, operation)
        if len(values) != 1:
            raise self._signature_error(operation)
        return values[0]

    def _extract_ret_code(self, result: Any) -> int | None:
        if self._is_ret(result):
            return int(result)
        if not self._is_sequence(result) or not result:
            return None
        if self._is_ret(result[-1]):
            return int(result[-1])
        if self._is_ret(result[0]):
            return int(result[0])
        return None

    def _is_success_ret(self, result: Any) -> bool:
        ret = self._extract_ret_code(result)
        return ret in (None, 0)

    def _payload_without_ret(self, result: Any, operation: str) -> list[Any]:
        if self._is_ret(result):
            check_ret(int(result), operation)
            return []
        if not self._is_sequence(result):
            return [result]

        values = list(result)
        if values and self._is_ret(values[-1]):
            check_ret(int(values[-1]), operation)
            return values[:-1]
        if values and self._is_ret(values[0]):
            check_ret(int(values[0]), operation)
            return values[1:]
        return values

    def _parse_get_version_result(self, result: Any) -> tuple[str, str | float]:
        values = self._payload_without_ret(result, "SapModel.GetVersion")
        if not values:
            raise self._signature_error("SapModel.GetVersion")
        version_label = str(values[0])
        version_number_raw = values[1] if len(values) > 1 else version_label
        version_number: str | float
        if isinstance(version_number_raw, (int, float)) and not isinstance(version_number_raw, bool):
            version_number = float(version_number_raw)
        else:
            version_number = str(version_number_raw)
        return version_label, version_number

    def _parse_get_name_list_result(self, result: Any) -> list[str]:
        values = self._payload_without_ret(result, "PointObj.GetNameList")
        count = self._first_int(values)
        names: list[str] = []
        for value in values:
            if self._is_sequence(value):
                names.extend(self._coerce_name_list(value))
            elif isinstance(value, str):
                names.append(value)
        if count == 0 and not names:
            return []
        if names:
            return names[:count] if count is not None and count >= 0 else names
        raise self._signature_error("PointObj.GetNameList")

    def _parse_get_coord_cartesian_result(self, result: Any, point_name: str) -> tuple[float, float, float]:
        values = self._payload_without_ret(result, f"PointObj.GetCoordCartesian({point_name})")
        numeric_values = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
        if len(numeric_values) < 3:
            raise self._signature_error(f"PointObj.GetCoordCartesian({point_name})")
        return numeric_values[0], numeric_values[1], numeric_values[2]

    def _parse_get_all_points_result(self, result: Any) -> list[tuple[str, float, float, float]]:
        values = self._payload_without_ret(result, "PointObj.GetAllPoints")
        count = self._first_int(values)
        if count == 0:
            return []

        sequences = [list(value) for value in values if self._is_sequence(value)]
        if len(sequences) < 4:
            raise self._signature_error("PointObj.GetAllPoints")

        names = self._coerce_name_list(sequences[0])
        x_values = self._coerce_float_list(sequences[1])
        y_values = self._coerce_float_list(sequences[2])
        z_values = self._coerce_float_list(sequences[3])
        row_count = count if count is not None and count >= 0 else min(len(names), len(x_values), len(y_values), len(z_values))
        if row_count == 0:
            return []
        if min(len(names), len(x_values), len(y_values), len(z_values)) < row_count:
            raise self._signature_error("PointObj.GetAllPoints")
        return [
            (names[index], x_values[index], y_values[index], z_values[index])
            for index in range(row_count)
        ]

    @staticmethod
    def _coerce_name_list(value) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, Iterable):
            names = [str(item) for item in value if isinstance(item, str) or item is not None]
            return [name for name in names if name]
        return []

    @staticmethod
    def _coerce_float_list(value) -> list[float]:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return [float(value)]
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [float(item) for item in value if isinstance(item, (int, float)) and not isinstance(item, bool)]
        return []

    @staticmethod
    def _first_int(values: list[Any]) -> int | None:
        for value in values:
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return None

    def _parse_xyz(self, values, point_name: str) -> tuple[float, float, float]:
        candidates = values if isinstance(values, tuple) else (values,)
        numeric_values = [float(value) for value in candidates if isinstance(value, (int, float))]
        if len(numeric_values) < 3:
            raise self._signature_error(f"PointObj.GetCoordCartesian({point_name})")
        return numeric_values[0], numeric_values[1], numeric_values[2]

    @staticmethod
    def _first_bool_sequence(values) -> list[bool] | None:
        candidates = values if isinstance(values, tuple) else (values,)
        for value in candidates:
            if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                flags = [bool(item) for item in value]
                if flags:
                    return flags
        return None

    @staticmethod
    def _is_ret(value) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def _is_sequence(value: Any) -> bool:
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))

    @classmethod
    def _has_ret_at_end(cls, values: tuple[object, ...]) -> bool:
        # A trailing 0 is the common successful SAP return-code shape. For longer
        # tuples, a trailing nonzero int is treated as a failed return code; for
        # two-value tuples it may be a version/unit value, so keep it as data.
        return bool(values) and cls._is_ret(values[-1]) and (values[-1] == 0 or len(values) > 2)

    @classmethod
    def _has_ret_at_start(cls, values: tuple[object, ...]) -> bool:
        # Some comtypes wrappers expose the return code first. Only a leading 0 is
        # treated as a return code until failed first-ret shapes are manually seen
        # on the target SAP2000 27 machine.
        return bool(values) and cls._is_ret(values[0]) and values[0] == 0

    @staticmethod
    def _units_from_raw(present_raw, database_raw) -> UnitsInfo:
        present_label = ComtypesSapAdapter._unit_label(present_raw)
        database_label = ComtypesSapAdapter._unit_label(database_raw)
        components = KNOWN_UNIT_COMPONENTS.get(present_raw if isinstance(present_raw, int) else -1, {})
        return UnitsInfo(
            present=present_label,
            database=database_label,
            present_raw=present_raw,
            database_raw=database_raw,
            length=components.get("length", "UNKNOWN"),
            force=components.get("force", "UNKNOWN"),
            moment=components.get("moment", "UNKNOWN"),
            temperature=components.get("temperature"),
        )

    @staticmethod
    def _unit_label(value) -> str:
        if isinstance(value, int) and value in KNOWN_UNIT_LABELS:
            return KNOWN_UNIT_LABELS[value]
        return f"UNKNOWN_ENUM_{value}"

    def _require_connected_object(self) -> None:
        if not self._connected or self._sap_object is None or self._sap_model is None:
            raise NotConnectedError()

    def _require_model(self) -> None:
        self._require_connected_object()
        if self._model_path is None:
            raise NoModelOpenError()

    @staticmethod
    def _placeholder(operation: str) -> BridgeError:
        return BridgeError(
            http_status=501,
            bridge_code="SAP2000_COM_PLACEHOLDER",
            message=f"ComtypesSapAdapter.{operation} is not implemented for real COM smoke. {VERIFY_ALL}.",
            retryable=False,
        )

    @staticmethod
    def _signature_error(operation: str) -> BridgeError:
        return BridgeError(
            http_status=501,
            bridge_code="SAP2000_COM_SIGNATURE_UNVERIFIED",
            message=f"Could not interpret SAP2000 COM return values for {operation}. {VERIFY_ALL}.",
            retryable=False,
        )


def _same_file(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve() or left.samefile(right)
    except (FileNotFoundError, OSError):
        return left.resolve() == right.resolve()
