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
    mock_router.get("/v1/transactions").respond(
        status_code=502, content=b"<html>Bad Gateway</html>", headers={"content-type": "text/html"}
    )

    with pytest.raises(BitpandaAPIError, match="Bad Gateway"):
        await bp_client.list_transactions()


async def test_extract_error_detail_plain_json(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns JSON without 'message' or 'errors' keys, falls back to resp.text."""
    mock_router.get("/v1/transactions").respond(status_code=500, json={"unexpected": "shape"})

    with pytest.raises(BitpandaAPIError):
        await bp_client.list_transactions()


async def test_extract_error_detail_errors_list_with_title(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/transactions").respond(
        status_code=401, json={"errors": [{"title": "Credentials wrong", "status": 401}]}
    )
    with pytest.raises(BitpandaAPIError, match="Credentials wrong"):
        await bp_client.list_transactions()


@patch("bitpanda_mcp.clients.base._MAX_PAGES", 2)
async def test_pagination_stops_at_max_pages(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """Pagination guard: stops after _MAX_PAGES even if API keeps returning a next_cursor."""

    def _always_full(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"transaction_id": "t1"},
                    {"transaction_id": "t2"},
                ],
                "page_size": 2,
                "end_cursor": "cursor-abc",
                "has_next_page": True,
            },
        )

    mock_router.get("/v1/transactions").mock(side_effect=_always_full)
    transactions = await bp_client.list_transactions(page_size=2)
    # _MAX_PAGES=2 -> 2 items per page x 2 pages = 4 items
    assert len(transactions) == 4


async def test_pagination_stops_on_short_page(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When a page says there is no next page, paginator stops."""
    calls = {"n": 0}

    def _two_pages(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            data = [
                {"transaction_id": "t1"},
                {"transaction_id": "t2"},
            ]
            has_next_page = True
        else:
            data = [{"transaction_id": "t3"}]
            has_next_page = False
        return httpx.Response(
            200,
            json={
                "data": data,
                "page_size": 2,
                "end_cursor": "cursor-page2",
                "has_next_page": has_next_page,
            },
        )

    mock_router.get("/v1/transactions").mock(side_effect=_two_pages)
    transactions = await bp_client.list_transactions(page_size=2)
    assert len(transactions) == 3
    assert calls["n"] == 2


async def test_pagination_stops_when_cursor_exhausted(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """When API returns no next_cursor on a full page, pagination stops."""
    calls = {"n": 0}

    def _two_full_pages(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {"transaction_id": f"t{calls['n']}a"},
                    {"transaction_id": f"t{calls['n']}b"},
                ],
                "page_size": 2,
                "end_cursor": "cursor-p2" if calls["n"] == 1 else "",
                "has_next_page": calls["n"] == 1,
            },
        )

    mock_router.get("/v1/transactions").mock(side_effect=_two_full_pages)
    transactions = await bp_client.list_transactions(page_size=2)
    assert len(transactions) == 4
    assert calls["n"] == 2


async def test_pagination_sends_cursor_in_subsequent_requests(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    """Verify the cursor value from page 1 is sent as a query param in page 2."""
    calls = {"n": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            assert "after" not in str(request.url)
            next_cursor = "cursor-xyz"
        else:
            assert "after=cursor-xyz" in str(request.url)
            next_cursor = ""
        return httpx.Response(
            200,
            json={
                "data": [{"transaction_id": f"t{calls['n']}"}],
                "page_size": 1,
                "end_cursor": next_cursor,
                "has_next_page": calls["n"] == 1,
            },
        )

    mock_router.get("/v1/transactions").mock(side_effect=_handler)
    transactions = await bp_client.list_transactions(page_size=1)
    assert len(transactions) == 2
    assert calls["n"] == 2


async def test_pagination_stops_when_next_page_has_no_cursor(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/transactions").respond(
        json={"data": [{"transaction_id": "t1"}], "has_next_page": True}
    )
    transactions = await bp_client.list_transactions(page_size=1)
    assert len(transactions) == 1


async def test_pagination_respects_limit(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json={
            "data": [
                {"transaction_id": "t1"},
                {"transaction_id": "t2"},
                {"transaction_id": "t3"},
            ],
            "page_size": 3,
            "has_next_page": False,
        }
    )
    transactions = await bp_client.list_transactions(page_size=3, limit=2)
    assert len(transactions) == 2


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


def test_flatten_jsonapi_type_without_id() -> None:
    raw = {"type": "wallet", "attributes": {"balance": "1.0"}}
    assert flatten_jsonapi(raw) == {"balance": "1.0", "type": "wallet"}


def test_flatten_jsonapi_passthrough_non_dict() -> None:
    assert flatten_jsonapi("not-a-dict") == "not-a-dict"


def test_flatten_jsonapi_no_attributes() -> None:
    raw = {"type": "thing", "id": "x", "other": "value"}
    assert flatten_jsonapi(raw) == raw
