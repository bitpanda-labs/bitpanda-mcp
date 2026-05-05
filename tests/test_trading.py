import httpx
import pytest
import respx
from fastmcp.exceptions import ToolError

from bitpanda_mcp.clients.bitpanda import BitpandaClient


def _transaction(tid: str, trade_type: str, asset_id: str, trade_id: str = "") -> dict:
    return {
        "transaction_id": tid,
        "operation_id": f"op-{tid}",
        "asset_id": asset_id,
        "account_id": "account-1",
        "wallet_id": "wallet-1",
        "asset_amount": "0.015",
        "fee_amount": "1.49",
        "operation_type": trade_type,
        "transaction_type": "trade",
        "flow": "incoming",
        "credited_at": "2026-04-20T10:00:00Z",
        "compensates": "",
        "trade_id": trade_id or f"trade-{tid}",
    }


def _page(records: list[dict], next_cursor: str = "") -> dict:
    return {"data": records, "end_cursor": next_cursor, "has_next_page": bool(next_cursor)}


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
            "price_change_day": "-2.0",
        },
    ],
    "has_next_page": False,
}


async def test_list_trades(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {})
    assert result.data["count"] == 2
    assert result.data["trades"][0]["type"] == "buy"
    assert result.data["trades"][0]["asset_symbol"] == "BTC"
    assert result.data["trades"][0]["price_eur"] == "65000.00"
    assert result.data["trades"][1]["type"] == "sell"


async def test_list_trades_filter_type(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"trade_type": "buy"})
    assert result.data["count"] == 1
    assert result.data["trades"][0]["type"] == "buy"


async def test_list_trades_operation_cli_alias(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"operation": "sell"})

    assert result.data["count"] == 1
    assert result.data["trades"][0]["type"] == "sell"


async def test_list_trades_rejects_conflicting_type_aliases(mcp_client) -> None:
    with pytest.raises(ToolError, match="Conflicting values"):
        await mcp_client.call_tool("list_trades", {"trade_type": "buy", "operation": "sell"})


async def test_list_trades_asset_type_and_date_filters(mcp_client, mock_router: respx.MockRouter) -> None:
    route = mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool(
        "list_trades",
        {
            "asset_type": "cryptocoin",
            "from_including": "2026-01-01",
            "to_excluding": "2026-02-01",
            "limit": 1,
        },
    )
    assert result.data["count"] == 1
    assert result.data["trades"][0]["asset_symbol"] == "BTC"
    url = str(route.calls[0].request.url)
    assert "from_including=2026-01-01" in url
    assert "to_excluding=2026-02-01" in url
    assert "page_size=25" in url


async def test_list_trades_asset_type_filters_out_missing_ticker(
    mcp_client, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/transactions").respond(json=_page([_transaction("tx1", "buy", "asset-unknown")]))
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"asset_type": "cryptocoin"})
    assert result.data == {"count": 0, "trades": []}


async def test_list_trades_respects_limit(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"limit": 1})
    assert result.data["count"] == 1
    assert result.data["trades"][0]["trade_id"] == "trade-tx1"


async def test_list_trades_limit_applies_after_trade_type_filter_across_pages(
    mcp_client, mock_router: respx.MockRouter
) -> None:
    calls = {"n": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json=_page([_transaction("tx1", "sell", "asset-btc")], "cursor-1"))
        assert "after=cursor-1" in str(request.url)
        return httpx.Response(200, json=_page([_transaction("tx2", "buy", "asset-eth")]))

    mock_router.get("/v1/transactions").mock(side_effect=_handler)
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"trade_type": "buy", "limit": 1, "page_size": 1})

    assert result.data["count"] == 1
    assert result.data["trades"][0]["trade_id"] == "trade-tx2"
    assert calls["n"] == 2


async def test_list_trades_limit_applies_after_asset_type_filter_across_pages(
    mcp_client, mock_router: respx.MockRouter
) -> None:
    calls = {"n": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            records = [_transaction(f"tx{i}", "buy", "asset-unknown") for i in range(5)]
            return httpx.Response(200, json=_page(records, "cursor-1"))
        if calls["n"] == 2:
            records = [_transaction(f"tx{i}", "buy", "asset-unknown") for i in range(5, 10)]
            return httpx.Response(200, json=_page(records, "cursor-2"))
        assert "after=cursor-2" in str(request.url)
        return httpx.Response(200, json=_page([_transaction("tx10", "buy", "asset-btc")]))

    mock_router.get("/v1/transactions").mock(side_effect=_handler)
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool(
        "list_trades", {"asset_type": "cryptocoin", "limit": 1, "page_size": 5}
    )

    assert result.data["count"] == 1
    assert result.data["trades"][0]["trade_id"] == "trade-tx10"
    assert calls["n"] == 3


async def test_list_trades_all_bypasses_limit(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json=_page([_transaction("tx1", "buy", "asset-btc"), _transaction("tx2", "sell", "asset-eth")])
    )
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {"all": True, "limit": 1})

    assert result.data["count"] == 2
    assert [trade["trade_id"] for trade in result.data["trades"]] == ["trade-tx1", "trade-tx2"]


async def test_list_trades_empty(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(json=_page([]))
    trades = await bp_client.list_trades(trade_type="buy")
    assert trades == []


async def test_list_trades_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(json=_page([{"operation_type": "buy"}]))
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("list_trades", {})


async def test_list_trades_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(status_code=500, json={"message": "Internal error"})

    with pytest.raises(ToolError, match="Internal error"):
        await mcp_client.call_tool("list_trades", {})


async def test_list_trades_missing_ticker_entry(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(json=_page([_transaction("tx1", "buy", "asset-unknown")]))
    mock_router.get("/v1/ticker").respond(json=TICKER_RESPONSE)

    result = await mcp_client.call_tool("list_trades", {})
    trade = result.data["trades"][0]
    assert trade["asset_symbol"] == ""
    assert trade["price_eur"] is None
