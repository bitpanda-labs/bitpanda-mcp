"""Tests for clients/base.py — error extraction, pagination, JSON:API flatten."""

from unittest.mock import patch

import httpx
import pytest
import respx

from bitpanda_mcp.clients.base import flatten_jsonapi
from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.models.common import BitpandaAPIError


async def test_extract_error_detail_non_json(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns HTML error, _extract_error_detail falls back to resp.text."""
    mock_router.get("/v1/trades").respond(
        status_code=502, content=b"<html>Bad Gateway</html>", headers={"content-type": "text/html"}
    )

    with pytest.raises(BitpandaAPIError, match="Bad Gateway"):
        await bp_client.list_trades()


async def test_extract_error_detail_plain_json(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns JSON without 'message' or 'errors' keys, falls back to resp.text."""
    mock_router.get("/v1/trades").respond(status_code=500, json={"unexpected": "shape"})

    with pytest.raises(BitpandaAPIError):
        await bp_client.list_trades()


async def test_extract_error_detail_errors_list_with_title(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/trades").respond(
        status_code=401, json={"errors": [{"title": "Credentials wrong", "status": 401}]}
    )
    with pytest.raises(BitpandaAPIError, match="Credentials wrong"):
        await bp_client.list_trades()


@patch("bitpanda_mcp.clients.base._MAX_PAGES", 2)
async def test_pagination_stops_at_max_pages(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """Pagination guard: stops after _MAX_PAGES even if API keeps returning full pages."""

    def _always_full(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"type": "trade", "id": "t1", "attributes": {"type": "buy"}},
                    {"type": "trade", "id": "t2", "attributes": {"type": "buy"}},
                ],
                "meta": {"total_count": 10000, "page_size": 2, "page": 1, "page_number": 1},
            },
        )

    mock_router.get("/v1/trades").mock(side_effect=_always_full)
    trades = await bp_client.list_trades(page_size=2)
    # _MAX_PAGES=2 -> 2 items per page x 2 pages = 4 items
    assert len(trades) == 4


async def test_pagination_stops_on_short_page(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When a page returns fewer items than page_size, paginator stops."""
    calls = {"n": 0}

    def _two_pages(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            data = [
                {"type": "trade", "id": "t1", "attributes": {"type": "buy"}},
                {"type": "trade", "id": "t2", "attributes": {"type": "buy"}},
            ]
        else:
            data = [{"type": "trade", "id": "t3", "attributes": {"type": "sell"}}]
        return httpx.Response(
            200,
            json={
                "data": data,
                "meta": {"total_count": 3, "page_size": 2, "page": calls["n"], "page_number": calls["n"]},
            },
        )

    mock_router.get("/v1/trades").mock(side_effect=_two_pages)
    trades = await bp_client.list_trades(page_size=2)
    assert len(trades) == 3
    assert calls["n"] == 2


async def test_pagination_stops_when_total_reached(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When accumulated items reach ``meta.total_count`` the paginator stops even if the
    last page was a full page (otherwise we'd loop forever on equal-total APIs)."""
    calls = {"n": 0}

    def _full_until_total(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {"type": "trade", "id": f"t{calls['n']}a", "attributes": {"type": "buy"}},
                    {"type": "trade", "id": f"t{calls['n']}b", "attributes": {"type": "buy"}},
                ],
                "meta": {"total_count": 4, "page_size": 2, "page": calls["n"], "page_number": calls["n"]},
            },
        )

    mock_router.get("/v1/trades").mock(side_effect=_full_until_total)
    trades = await bp_client.list_trades(page_size=2)
    assert len(trades) == 4
    assert calls["n"] == 2


async def test_pagination_respects_limit(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/trades").respond(
        json={
            "data": [
                {"type": "trade", "id": "t1", "attributes": {"type": "buy"}},
                {"type": "trade", "id": "t2", "attributes": {"type": "buy"}},
                {"type": "trade", "id": "t3", "attributes": {"type": "buy"}},
            ],
            "meta": {"total_count": 3, "page_size": 3, "page": 1, "page_number": 1},
        }
    )
    trades = await bp_client.list_trades(page_size=3, limit=2)
    assert len(trades) == 2


async def test_network_error_raises_api_error(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/ticker").mock(side_effect=httpx.ConnectError("Connection refused"))
    with pytest.raises(BitpandaAPIError, match="Network error"):
        await bp_client.fetch_ticker()


async def test_invalid_json_raises_api_error(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/ticker").respond(
        status_code=200, content=b"<html>Maintenance</html>", headers={"content-type": "text/html"}
    )
    with pytest.raises(BitpandaAPIError, match="Invalid JSON"):
        await bp_client.fetch_ticker()


def test_is_auth_error() -> None:
    err_401 = BitpandaAPIError(401, "Unauthorized")
    err_403 = BitpandaAPIError(403, "Forbidden")
    err_500 = BitpandaAPIError(500, "Internal error")

    assert err_401.is_auth_error is True
    assert err_403.is_auth_error is True
    assert err_500.is_auth_error is False


def test_flatten_jsonapi_standard_record() -> None:
    raw = {"type": "wallet", "id": "w1", "attributes": {"balance": "1.0", "name": "BTC Wallet"}}
    out = flatten_jsonapi(raw)
    assert out == {"balance": "1.0", "name": "BTC Wallet", "id": "w1", "type": "wallet"}


def test_flatten_jsonapi_attrs_type_wins() -> None:
    """When attributes has its own 'type' (e.g. trade 'buy'), envelope type is not overwritten."""
    raw = {"type": "trade", "id": "t1", "attributes": {"type": "buy", "price": "100"}}
    out = flatten_jsonapi(raw)
    assert out["type"] == "buy"


def test_flatten_jsonapi_passthrough_non_dict() -> None:
    assert flatten_jsonapi("not-a-dict") == "not-a-dict"  # type: ignore[arg-type]


def test_flatten_jsonapi_no_attributes() -> None:
    raw = {"type": "thing", "id": "x", "other": "value"}
    assert flatten_jsonapi(raw) == raw
