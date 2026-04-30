from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.tools.portfolio import get_portfolio


def _wallet(wid: str, asset_id: str, balance: str) -> dict:
    return {
        "wallet_id": wid,
        "asset_id": asset_id,
        "wallet_type": "",
        "index_asset_id": "",
        "last_credited_at": "2026-04-20T10:00:00Z",
        "balance": balance,
    }


WALLETS_RESPONSE = {
    "data": [
        _wallet("w1", "asset-btc", "0.5"),
        _wallet("w2", "asset-eth", "2.0"),
        _wallet("w3", "asset-doge", "0.0"),
        _wallet("w4", "asset-unknown", "100.0"),
    ],
    "has_next_page": False,
}

TICKER_RESPONSE = {
    "data": [
        {
            "id": "asset-btc",
            "name": "Bitcoin",
            "symbol": "BTC",
            "type": "cryptocoin",
            "currency": "EUR",
            "price": "65000.00",
            "price_change_day": "1.0",
        },
        {
            "id": "asset-eth",
            "name": "Ethereum",
            "symbol": "ETH",
            "type": "cryptocoin",
            "currency": "EUR",
            "price": "3500.00",
            "price_change_day": "2.0",
        },
        {
            "id": "asset-doge",
            "name": "Dogecoin",
            "symbol": "DOGE",
            "type": "cryptocoin",
            "currency": "EUR",
            "price": "0.10",
            "price_change_day": "0",
        },
    ],
    "has_next_page": False,
}


async def test_get_portfolio(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json=WALLETS_RESPONSE)
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_portfolio", {})
    data = result.data
    assert data["count"] == 2
    assert data["total_value_eur"] == 39500.0

    assert data["holdings"][0]["symbol"] == "BTC"
    assert data["holdings"][0]["value_eur"] == 32500.0
    assert data["holdings"][1]["symbol"] == "ETH"
    assert data["holdings"][1]["value_eur"] == 7000.0
    assert data["skipped_asset_ids"] == ["asset-unknown"]


async def test_get_portfolio_sort_by_name(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json=WALLETS_RESPONSE)
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_portfolio", {"sort_by": "name"})
    holdings = result.data["holdings"]
    assert [h["symbol"] for h in holdings] == ["BTC", "ETH"]


async def test_get_portfolio_sort_cli_alias(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json=WALLETS_RESPONSE)
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_portfolio", {"sort": "name"})
    holdings = result.data["holdings"]
    assert [h["symbol"] for h in holdings] == ["BTC", "ETH"]


async def test_get_portfolio_rejects_conflicting_sort_aliases(mcp_client) -> None:
    with pytest.raises(ToolError, match="Conflicting values"):
        await mcp_client.call_tool("get_portfolio", {"sort": "name", "sort_by": "value"})


async def test_get_portfolio_rejects_unknown_sort(mcp_client) -> None:
    with pytest.raises(ToolError, match="must be either"):
        await mcp_client.call_tool("get_portfolio", {"sort": "symbol"})


async def test_get_portfolio_non_numeric_price(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json={"data": [_wallet("w1", "asset-brk", "10.0")]})
    mock_router.get("/v1/ticker").respond(
        json={
            "data": [
                {
                    "id": "asset-brk",
                    "name": "Broken",
                    "symbol": "BRK",
                    "type": "cryptocoin",
                    "currency": "EUR",
                    "price": "not-a-number",
                }
            ],
            "has_next_page": False,
        }
    )

    result = await mcp_client.call_tool("get_portfolio", {})
    assert result.data["holdings"][0]["value_eur"] == 0.0


async def test_get_portfolio_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(ToolError, match="Unauthorized"):
        await mcp_client.call_tool("get_portfolio", {})


async def test_get_portfolio_skips_wallet_without_asset_id(mcp_client, mock_router: respx.MockRouter) -> None:
    empty_asset_wallet = _wallet("w1", "", "1.0")
    mock_router.get("/v1/wallets/").respond(
        json={"data": [empty_asset_wallet, _wallet("w2", "asset-btc", "0.5")]}
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("get_portfolio", {})
    assert [h["symbol"] for h in result.data["holdings"]] == ["BTC"]


async def test_get_portfolio_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_wallets = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Wallet", [{"type": "missing", "loc": ("wallet_id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.portfolio.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await get_portfolio(ctx)
