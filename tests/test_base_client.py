"""Tests for clients/base.py — error extraction, pagination edge cases."""

from unittest.mock import patch

import httpx
import pytest
import respx

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.models.common import BitpandaAPIError


async def test_extract_error_detail_non_json(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns HTML error, _extract_error_detail falls back to resp.text."""
    mock_router.get("/v1/assets/x").respond(
        status_code=502, content=b"<html>Bad Gateway</html>", headers={"content-type": "text/html"}
    )

    with pytest.raises(BitpandaAPIError, match="Bad Gateway"):
        await bp_client.get_asset("x")


async def test_extract_error_detail_plain_text_json(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns JSON without 'message' or 'errors' keys, falls back to resp.text."""
    mock_router.get("/v1/assets/x").respond(status_code=500, json={"unexpected": "shape"})

    with pytest.raises(BitpandaAPIError):
        await bp_client.get_asset("x")


@patch("bitpanda_mcp.clients.base._MAX_PAGES", 2)
async def test_pagination_stops_at_max_pages(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """Pagination guard: stops after _MAX_PAGES even if API keeps returning has_next_page=True."""

    def _infinite_pages(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [{"id": "item"}],
                "has_next_page": True,
                "end_cursor": "next",
                "page_size": 1,
            },
        )

    mock_router.get("/v1/assets").mock(side_effect=_infinite_pages)
    items = await bp_client.list_assets(page_size=1)
    assert len(items) == 2


def test_is_auth_error() -> None:
    err_401 = BitpandaAPIError(401, "Unauthorized")
    err_403 = BitpandaAPIError(403, "Forbidden")
    err_500 = BitpandaAPIError(500, "Internal error")

    assert err_401.is_auth_error is True
    assert err_403.is_auth_error is True
    assert err_500.is_auth_error is False
