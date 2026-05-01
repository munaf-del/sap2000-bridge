from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from bridge.config import Settings


ROOT = Path(__file__).resolve().parents[1]


def cors_client(settings: Settings) -> TestClient:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    )

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def preflight(client: TestClient, origin: str):
    return client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )


def test_localhost_3000_preflight_allowed() -> None:
    response = preflight(cors_client(Settings()), "http://localhost:3000")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_127_0_0_1_3000_preflight_allowed() -> None:
    response = preflight(cors_client(Settings()), "http://127.0.0.1:3000")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_configured_office_wsl_origin_preflight_allowed(monkeypatch) -> None:
    monkeypatch.setenv("SAP2000_BRIDGE_ALLOWED_ORIGINS", "http://10.0.1.252:3000")
    response = preflight(cors_client(Settings()), "http://10.0.1.252:3000")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://10.0.1.252:3000"


def test_unconfigured_random_origin_is_not_allowed() -> None:
    response = preflight(cors_client(Settings()), "http://evil.example:3000")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_wildcard_cors_origin_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("SAP2000_BRIDGE_ALLOWED_ORIGINS", "*")

    with pytest.raises(ValueError, match="Wildcard CORS origins are not allowed"):
        Settings()


def test_source_scripts_and_config_do_not_bind_to_all_interfaces() -> None:
    checked_paths = [
        *list((ROOT / "src").rglob("*.py")),
        *list((ROOT / "scripts").rglob("*.ps1")),
        ROOT / "pyproject.toml",
    ]

    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        assert "0.0.0.0" not in text

