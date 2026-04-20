import pytest
import respx
from fastmcp.exceptions import ToolError

from bitpanda_mcp.clients.bitpanda import BitpandaClient


def _trade(tid: str, trade_type: str, symbol: str, amount_fiat: str, amount_crypto: str) -> dict:
    return {
        "type": "trade",
        "id": tid,
        "attributes": {
            "type": trade_type,
            "status": "finished",
            "cryptocoin_id": "1",
            "cryptocoin_symbol": symbol,
            "fiat_id": "1",
            "amount_fiat": amount_fiat,
            "amount_cryptocoin": amount_crypto,
            "price": "65000.00",
            "fee": "1.49",
        },
    }


TRADES_RESPONSE = {
    "data": [
        _trade("trade-1", "buy", "BTC", "1000.00", "0.015"),
        _trade("trade-2", "sell", "ETH", "500.00", "0.15"),
    ],
    "meta": {"total_count": 2, "page_size": 25, "page": 1, "page_number": 1},
    "links": {"self": "?page_number=1&page_size=25"},
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
        "meta": {"total_count": 1, "page_size": 25, "page": 1, "page_number": 1},
    }
    route = mock_router.get("/v1/trades").respond(json=buy_only)

    result = await mcp_client.call_tool("list_trades", {"trade_type": "buy"})
    assert result.data["count"] == 1
    assert result.data["trades"][0]["type"] == "buy"
    assert "type=buy" in str(route.calls[0].request.url)


async def test_list_trades_empty(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/trades").respond(
        json={"data": [], "meta": {"total_count": 0, "page_size": 25, "page": 1, "page_number": 1}}
    )
    trades = await bp_client.list_trades(trade_type="buy")
    assert trades == []


async def test_list_trades_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    """A record missing the required ``id`` field fails Trade validation."""
    mock_router.get("/v1/trades").respond(
        json={"data": [{"type": "trade", "attributes": {"type": "buy"}}], "meta": {"total_count": 1}}
    )
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("list_trades", {})


async def test_list_trades_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/trades").respond(status_code=500, json={"message": "Internal error"})

    with pytest.raises(ToolError, match="Internal error"):
        await mcp_client.call_tool("list_trades", {})
