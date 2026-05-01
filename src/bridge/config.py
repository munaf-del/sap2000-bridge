from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAP2000_BRIDGE_", extra="ignore", populate_by_name=True)

    service_name: str = "sap2000-local-bridge"
    bridge_version: str = "0.1.0"
    host: str = "127.0.0.1"
    adapter_mode: Literal["fake", "comtypes"] = "fake"
    csi_products_root: str | None = r"C:\Program Files\Computers and Structures"
    sap2000_install_dir: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27"
    sap2000_exe_path: str | None = Field(
        default=r"C:\Program Files\Computers and Structures\SAP2000 27\SAP2000.exe",
        validation_alias=AliasChoices("SAP2000_EXE_PATH", "SAP2000_BRIDGE_SAP2000_EXE_PATH"),
    )
    sap2000_api_dll_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\SAP2000v1.dll"
    csi_api_dll_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\CSiAPIv1.dll"
    sap2000_oapi_chm_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\CSI_OAPI_Documentation.chm"
    sap2000_model_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SAP2000_MODEL_PATH", "SAP2000_BRIDGE_SAP2000_MODEL_PATH"),
    )
    sap2000_workspace: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SAP2000_WORKSPACE", "SAP2000_BRIDGE_SAP2000_WORKSPACE"),
    )
    enable_real_com: bool = Field(
        default=False,
        validation_alias=AliasChoices("SAP2000_BRIDGE_ENABLE_REAL_COM"),
    )
    read_only: bool = True
    writeback_enabled: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1", "http://localhost"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
