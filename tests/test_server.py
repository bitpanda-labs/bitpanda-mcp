"""Tests for server.py — health endpoint, version, and lifespan."""

from unittest.mock import AsyncMock, patch

import httpx
from starlette.middleware import Middleware
from starlette.testclient import TestClient

from bitpanda_mcp import __version__
from bitpanda_mcp.auth import ApiKeyHeaderMiddleware
from bitpanda_mcp.config import Settings
from bitpanda_mcp.server import lifespan, mcp


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


def test_oauth_authorization_server_metadata() -> None:
    app = mcp.http_app()
    client = TestClient(app, base_url="http://testserver")
    resp = client.get("/.well-known/oauth-authorization-server")
    assert resp.status_code == 200
    data = resp.json()
    assert data["issuer"] == "http://testserver"
    assert data["grant_types_supported"] == []


def test_oauth_protected_resource_metadata() -> None:
    app = mcp.http_app()
    client = TestClient(app, base_url="http://testserver")
    resp = client.get("/.well-known/oauth-protected-resource")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resource"] == "http://testserver/mcp"
    assert data["bearer_methods_supported"] == ["header"]


def test_http_app_accepts_api_key_middleware() -> None:
    app = mcp.http_app(middleware=[Middleware(ApiKeyHeaderMiddleware, header_name="X-Api-Key")])
    client = TestClient(app)
    assert client.get("/healthz").status_code == 200


async def test_lifespan_with_api_key() -> None:
    settings = Settings(bitpanda_api_key="test-key-123", _env_file=None)
    with patch("bitpanda_mcp.server.Settings", return_value=settings):
        mock_server = AsyncMock()
        async with lifespan(mock_server) as ctx:
            assert "http" in ctx
            assert "bp" in ctx
            assert isinstance(ctx["http"], httpx.AsyncClient)


async def test_lifespan_without_api_key() -> None:
    settings = Settings(bitpanda_api_key=None, _env_file=None)
    with patch("bitpanda_mcp.server.Settings", return_value=settings):
        mock_server = AsyncMock()
        async with lifespan(mock_server) as ctx:
            assert "http" in ctx
            assert "bp" not in ctx
