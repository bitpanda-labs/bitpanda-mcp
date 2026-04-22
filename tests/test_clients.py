"""Tests for clients/__init__.py — get_bp_client in both modes."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.clients.bitpanda import BitpandaClient

SAMPLE_KEY = "user-api-key-abc123"


def _make_ctx(lifespan_context: dict) -> MagicMock:
    ctx = MagicMock()
    ctx.lifespan_context = lifespan_context
    return ctx


def test_get_bp_client_stdio_mode() -> None:
    bp = MagicMock(spec=BitpandaClient)
    ctx = _make_ctx({"http": MagicMock(), "bp": bp})
    result = get_bp_client(ctx)
    assert result is bp


@patch("bitpanda_mcp.clients.get_access_token")
async def test_get_bp_client_http_mode(mock_get_token: MagicMock) -> None:
    mock_get_token.return_value = AccessToken(token=SAMPLE_KEY, client_id="bearer", scopes=[])
    async with httpx.AsyncClient(base_url="https://test.bitpanda.com") as http:
        ctx = _make_ctx({"http": http})
        result = get_bp_client(ctx)
        assert isinstance(result, BitpandaClient)


@patch("bitpanda_mcp.clients.get_access_token")
def test_get_bp_client_no_token_raises(mock_get_token: MagicMock) -> None:
    mock_get_token.return_value = None
    ctx = _make_ctx({"http": MagicMock()})

    with pytest.raises(ToolError, match="Authentication required"):
        get_bp_client(ctx)
