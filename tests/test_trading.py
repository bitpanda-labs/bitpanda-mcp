import pytest
import respx
from fastmcp.exceptions import ToolError

TRADES_RESPONSE = {
    "data": [
        {
            "id": "trade-1",
            "type": "buy",
            "status": "finished",
            "cryptocoin_id": "a-btc",
            "cryptocoin_symbol": "BTC",
            "fiat_id": "f-eur",
            "amount_fiat": "1000.00",
            "amount_cryptocoin": "0.015",
            "price": "65000.00",
            "fee": "1.49",
            "time": "2025-06-01T12:00:00Z",
        },
        {
            "id": "trade-2",
            "type": "sell",
            "status": "finished",
            "cryptocoin_id": "a-eth",
            "cryptocoin_symbol": "ETH",
            "fiat_id": "f-eur",
            "amount_fiat": "500.00",
            "amount_cryptocoin": "0.15",
            "price": "3500.00",
            "fee": "0.75",
            "time": "2025-06-02T10:00:00Z",
        },
    ],
    "has_next_page": False,
    "page_size": 25,
}


async def test_list_trades(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/trades").respond(json=TRADES_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {})
    assert result.data["count"] == 2
    assert result.data["trades"][0]["type"] == "buy"
    assert result.data["trades"][0]["cryptocoin_symbol"] == "BTC"
    assert result.data["trades"][1]["type"] == "sell"


async def test_list_trades_filter_type(mcp_client, mock_router: respx.MockRouter) -> None:
    buy_only = {
        "data": [TRADES_RESPONSE["data"][0]],
        "has_next_page": False,
        "page_size": 25,
    }
    mock_router.get("/v1/trades").respond(json=buy_only)

    result = await mcp_client.call_tool("list_trades", {"trade_type": "buy"})
    assert result.data["count"] == 1
    assert result.data["trades"][0]["type"] == "buy"


async def test_list_trades_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/trades").respond(status_code=500, json={"message": "Internal error"})

    with pytest.raises(ToolError, match="Internal error"):
        await mcp_client.call_tool("list_trades", {})
