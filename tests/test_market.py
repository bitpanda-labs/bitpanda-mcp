import pytest
import respx
from fastmcp.exceptions import ToolError

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


async def test_get_price(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_DATA)

    result = await mcp_client.call_tool("get_price", {"symbol": "BTC"})
    assert result.data["symbol"] == "BTC"
    assert result.data["price_eur"] == "65000.00"
    assert result.data["change_24h"] == "2.5"


async def test_get_price_case_insensitive(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_DATA)

    result = await mcp_client.call_tool("get_price", {"symbol": "btc"})
    assert result.data["symbol"] == "BTC"


async def test_get_price_not_found(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_DATA)

    with pytest.raises(ToolError, match="DOGE"):
        await mcp_client.call_tool("get_price", {"symbol": "DOGE"})


async def test_get_price_api_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(status_code=500, json={"message": "Server error"})

    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})
