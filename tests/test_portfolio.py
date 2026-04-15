import httpx
import pytest
import respx
from fastmcp.exceptions import ToolError


def _wallet_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "data": [
                {
                    "wallet_id": "w1",
                    "asset_id": "a-btc",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-01T00:00:00Z",
                    "balance": 0.5,
                },
                {
                    "wallet_id": "w2",
                    "asset_id": "a-eth",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-02T00:00:00Z",
                    "balance": 2.0,
                },
                {
                    "wallet_id": "w3",
                    "asset_id": "a-doge",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-03T00:00:00Z",
                    "balance": 0.0,
                },
                {
                    "wallet_id": "w4",
                    "asset_id": "a-unknown",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-04T00:00:00Z",
                    "balance": 100.0,
                },
            ],
            "has_next_page": False,
            "page_size": 25,
        },
    )


TICKER_DATA = {
    "data": [
        {
            "id": "a-btc",
            "name": "Bitcoin",
            "symbol": "BTC",
            "type": "cryptocoin",
            "price": "65000.00",
            "price_change_day": "2.5",
        },
        {
            "id": "a-eth",
            "name": "Ethereum",
            "symbol": "ETH",
            "type": "cryptocoin",
            "price": "3500.00",
            "price_change_day": "-1.2",
        },
    ],
    "has_next_page": False,
    "page_size": 100,
}


async def test_get_portfolio(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").mock(side_effect=_wallet_handler)
    mock_router.get("/v1/ticker").respond(json=TICKER_DATA)

    result = await mcp_client.call_tool("get_portfolio", {})
    data = result.data
    assert data["count"] == 2
    assert data["total_value_eur"] == 39500.0

    # Default sort by value desc: BTC (32500) > ETH (7000)
    assert data["holdings"][0]["symbol"] == "BTC"
    assert data["holdings"][0]["value_eur"] == 32500.0
    assert data["holdings"][1]["symbol"] == "ETH"
    assert data["holdings"][1]["value_eur"] == 7000.0

    # a-unknown has balance but is missing from ticker — surfaced, not silently dropped
    assert data["skipped_asset_ids"] == ["a-unknown"]


async def test_get_portfolio_sort_by_name(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").mock(side_effect=_wallet_handler)
    mock_router.get("/v1/ticker").respond(json=TICKER_DATA)

    result = await mcp_client.call_tool("get_portfolio", {"sort_by": "name"})
    holdings = result.data["holdings"]
    # Sorted alphabetically by asset name
    assert holdings[0]["name"] == "Bitcoin"
    assert holdings[1]["name"] == "Ethereum"


async def test_get_portfolio_non_numeric_price(mcp_client, mock_router: respx.MockRouter) -> None:
    """Non-numeric ticker price falls back to 0."""
    mock_router.get("/v1/wallets/").respond(
        json={
            "data": [
                {
                    "wallet_id": "w1",
                    "asset_id": "a1",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-01T00:00:00Z",
                    "balance": 10.0,
                },
            ],
            "has_next_page": False,
            "page_size": 25,
        },
    )
    mock_router.get("/v1/ticker").respond(
        json={
            "data": [
                {
                    "id": "a1",
                    "name": "Broken",
                    "symbol": "BRK",
                    "price": "not-a-number",
                    "price_change_day": "0",
                    "type": "test",
                },
            ],
            "has_next_page": False,
            "page_size": 100,
        },
    )

    result = await mcp_client.call_tool("get_portfolio", {})
    assert result.data["holdings"][0]["value_eur"] == 0.0


async def test_get_portfolio_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json={"data": [{"bad": "shape"}], "has_next_page": False})
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("get_portfolio", {})


async def test_get_portfolio_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(ToolError, match="Unauthorized"):
        await mcp_client.call_tool("get_portfolio", {})
