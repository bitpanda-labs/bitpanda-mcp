from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.tools.market import get_price, list_prices

TICKER_RESPONSE = {
    "data": [
        {
            "id": "asset-btc",
            "symbol": "BTC",
            "name": "Bitcoin",
            "type": "cryptocoin",
            "currency": "EUR",
            "price": "65000.00",
            "price_change_day": "-1.5",
        },
        {
            "id": "asset-eth",
            "symbol": "ETH",
            "name": "Ethereum",
            "type": "cryptocoin",
            "currency": "EUR",
            "price": "3500.00",
            "price_change_day": "2.3",
        },
        {
            "id": "asset-noeur",
            "symbol": "NOPRICE",
            "name": "No EUR",
            "type": "cryptocoin",
            "currency": "USD",
            "price": "1.00",
            "price_change_day": "0",
        },
    ],
    "has_next_page": False,
}


async def test_get_price(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_price", {"symbol": "BTC"})
    assert result.data["symbol"] == "BTC"
    assert result.data["name"] == "Bitcoin"
    assert result.data["asset_id"] == "asset-btc"
    assert result.data["type"] == "cryptocoin"
    assert result.data["currency"] == "EUR"
    assert result.data["price"] == "65000.00"
    assert result.data["price_eur"] == "65000.00"
    assert result.data["price_change_day"] == "-1.5"


async def test_get_price_case_insensitive(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_price", {"symbol": "btc"})
    assert result.data["symbol"] == "BTC"


async def test_get_price_not_found(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    with pytest.raises(ToolError, match="DOGE"):
        await mcp_client.call_tool("get_price", {"symbol": "DOGE"})


async def test_get_price_returns_non_eur_currency(mcp_client, mock_router: respx.MockRouter) -> None:
    """Ticker entries match the CLI and keep their quoted currency."""
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_price", {"symbol": "NOPRICE"})
    assert result.data["symbol"] == "NOPRICE"
    assert result.data["currency"] == "USD"
    assert result.data["price"] == "1.00"
    assert result.data["price_eur"] == "0"


async def test_get_price_non_dict_response(mcp_client, mock_router: respx.MockRouter) -> None:
    """If the ticker returns something other than a dict, the tool reports it."""
    mock_router.get("/v1/ticker").respond(json=[])

    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_api_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(status_code=500, json={"message": "Server error"})

    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_invalid_ticker_entry(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json={"data": [{"id": "asset-btc", "symbol": "BTC"}]})

    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_validation_error_direct() -> None:
    """Direct call covers ``except ValidationError`` in get_price."""
    ctx = MagicMock()
    bp = MagicMock()
    bp.fetch_ticker = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "TickerEntry", [{"type": "missing", "loc": ("symbol",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.market.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await get_price(ctx, "BTC")


async def test_list_prices_for_held_assets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)
    mock_router.get("/v1/wallets/").respond(
        json={
            "data": [
                {"wallet_id": "w1", "asset_id": "asset-btc", "balance": "1.0"},
                {"wallet_id": "w2", "asset_id": "asset-eth", "balance": "0.0"},
                {"wallet_id": "w3", "asset_id": "asset-missing", "balance": "2.0"},
            ],
            "has_next_page": False,
        }
    )

    result = await mcp_client.call_tool("list_prices", {})
    assert result.data["count"] == 1
    assert result.data["total_available"] == 1
    assert result.data["prices"][0]["symbol"] == "BTC"
    assert result.data["skipped_asset_ids"] == ["asset-missing"]


async def test_list_prices_all_assets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_prices", {"all_assets": True})
    assert result.data["count"] == 3
    assert result.data["total_available"] == 3
    assert [item["symbol"] for item in result.data["prices"]] == ["BTC", "ETH", "NOPRICE"]


async def test_list_prices_all_cli_alias(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_prices", {"all": True})

    assert result.data["count"] == 3


async def test_list_prices_limit_caps_returned_rows(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_prices", {"all": True, "limit": 2})

    assert result.data["count"] == 2
    assert result.data["total_available"] == 3
    assert [item["symbol"] for item in result.data["prices"]] == ["BTC", "ETH"]


async def test_list_prices_limit_zero_returns_all_rows(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_prices", {"all": True, "limit": 0})

    assert result.data["count"] == 3
    assert result.data["total_available"] == 3


async def test_list_prices_api_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(status_code=500, json={"message": "Server error"})

    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_prices", {})


async def test_list_prices_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.fetch_ticker = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "TickerEntry", [{"type": "missing", "loc": ("symbol",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.market.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await list_prices(ctx)
