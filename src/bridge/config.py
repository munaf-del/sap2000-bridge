from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAP2000_BRIDGE_", extra="ignore")

    service_name: str = "sap2000-local-bridge"
    bridge_version: str = "0.1.0"
    host: str = "127.0.0.1"
    adapter_mode: Literal["fake", "comtypes"] = "fake"
    csi_products_root: str | None = r"C:\Program Files\Computers and Structures"
    sap2000_install_dir: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27"
    sap2000_exe_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\SAP2000.exe"
    sap2000_api_dll_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\SAP2000v1.dll"
    csi_api_dll_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\CSiAPIv1.dll"
    sap2000_oapi_chm_path: str | None = r"C:\Program Files\Computers and Structures\SAP2000 27\CSI_OAPI_Documentation.chm"
    read_only: bool = True
    writeback_enabled: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1", "http://localhost"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
