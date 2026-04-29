from unittest.mock import AsyncMock, patch

import httpx
import pytest
from starlette.testclient import TestClient

from bitpanda_mcp import __version__
from bitpanda_mcp.auth import ApiKeyHeaderMiddleware
from bitpanda_mcp.config import Settings
from bitpanda_mcp.server import build_http_app, lifespan, mcp


def test_version_is_set() -> None:
    assert __version__
    assert __version__ != "0.0.0"


def test_server_version_matches_package() -> None:
    assert mcp._mcp_server.version == __version__


def test_health_endpoint() -> None:
    app = mcp.http_app()
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_oauth_well_known_routes_are_not_published() -> None:
    app = mcp.http_app()
    client = TestClient(app)
    assert client.get("/.well-known/oauth-authorization-server").status_code == 404
    assert client.get("/.well-known/oauth-protected-resource").status_code == 404


def _initialize_request() -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "t", "version": "0"},
        },
        "id": 1,
    }


def _mcp_headers(extra: dict[str, str]) -> dict[str, str]:
    return {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        **extra,
    }


def test_build_http_app_without_auth_header_does_not_wrap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_AUTH_HEADER", raising=False)
    settings = Settings(_env_file=None, FASTMCP_TRANSPORT="streamable-http")
    app = build_http_app(settings)
    assert not isinstance(app, ApiKeyHeaderMiddleware)


def test_build_http_app_with_auth_header_wraps_with_middleware() -> None:
    settings = Settings(_env_file=None, FASTMCP_TRANSPORT="streamable-http", MCP_AUTH_HEADER="X-Api-Key")
    app = build_http_app(settings)
    assert isinstance(app, ApiKeyHeaderMiddleware)


def test_build_http_app_rewrites_x_api_key_to_bearer() -> None:
    settings = Settings(_env_file=None, FASTMCP_TRANSPORT="streamable-http", MCP_AUTH_HEADER="X-Api-Key")
    app = build_http_app(settings)
    with TestClient(app) as client:
        resp = client.post(
            "/mcp",
            headers=_mcp_headers({"X-Api-Key": "test-token-123"}),
            json=_initialize_request(),
        )
        assert resp.status_code == 200


def test_build_http_app_rejects_request_without_credentials_when_header_set() -> None:
    settings = Settings(_env_file=None, FASTMCP_TRANSPORT="streamable-http", MCP_AUTH_HEADER="X-Api-Key")
    app = build_http_app(settings)
    with TestClient(app) as client:
        resp = client.post("/mcp", headers=_mcp_headers({}), json=_initialize_request())
        assert resp.status_code == 401


async def test_lifespan_with_api_key() -> None:
    settings = Settings(
        bitpanda_api_key="test-key-123", _env_file=None, FASTMCP_TRANSPORT="stdio"
    )
    with patch("bitpanda_mcp.server.Settings", return_value=settings):
        mock_server = AsyncMock()
        async with lifespan(mock_server) as ctx:
            assert "http" in ctx
            assert "bp" in ctx
            assert isinstance(ctx["http"], httpx.AsyncClient)


async def test_lifespan_without_api_key() -> None:
    settings = Settings(bitpanda_api_key=None, _env_file=None, FASTMCP_TRANSPORT="stdio")
    with patch("bitpanda_mcp.server.Settings", return_value=settings):
        mock_server = AsyncMock()
        async with lifespan(mock_server) as ctx:
            assert "http" in ctx
            assert "bp" not in ctx


async def test_lifespan_http_mode_ignores_env_api_key() -> None:
    settings = Settings(
        bitpanda_api_key="env-admin-key",
        _env_file=None,
        FASTMCP_TRANSPORT="streamable-http",
    )
    with patch("bitpanda_mcp.server.Settings", return_value=settings):
        mock_server = AsyncMock()
        async with lifespan(mock_server) as ctx:
            assert "http" in ctx
            assert "bp" not in ctx
