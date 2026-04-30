from unittest.mock import AsyncMock, MagicMock

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.tools.transactions import list_transactions


def _transaction(tid: str, operation_type: str, flow: str = "incoming") -> dict:
    return {
        "transaction_id": tid,
        "operation_id": f"op-{tid}",
        "asset_id": "asset-btc",
        "account_id": "account-1",
        "wallet_id": "wallet-1",
        "asset_amount": "0.1",
        "fee_amount": "0.00000000",
        "operation_type": operation_type,
        "transaction_type": "transfer",
        "flow": flow,
        "credited_at": "2026-04-20T10:00:00Z",
        "compensates": "",
        "trade_id": "",
    }


def _page(records: list[dict], page_size: int = 25, next_cursor: str = "") -> dict:
    return {
        "data": records,
        "page_size": page_size,
        "end_cursor": next_cursor,
        "has_next_page": bool(next_cursor),
    }


async def test_list_transactions_filters(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    route = mock_router.get("/v1/transactions").respond(json=_page([]))
    items = await bp_client.list_transactions(
        wallet_id="wallet-1",
        flow="incoming",
        asset_id="asset-btc",
        from_including="2026-01-01",
        to_excluding="2026-02-01",
    )
    assert items == []
    url = str(route.calls[0].request.url)
    assert "wallet_id=wallet-1" in url
    assert "flow=incoming" in url
    assert "asset_id=asset-btc" in url
    assert "from_including=2026-01-01" in url
    assert "to_excluding=2026-02-01" in url


async def test_list_transactions_tool_filters(mcp_client, mock_router: respx.MockRouter) -> None:
    route = mock_router.get("/v1/transactions").respond(json=_page([_transaction("tx1", "deposit")]))
    result = await mcp_client.call_tool(
        "list_transactions",
        {
            "wallet_id": "wallet-1",
            "flow": "incoming",
            "asset_id": "asset-btc",
            "from_including": "2026-01-01",
            "to_excluding": "2026-02-01",
            "limit": 1,
        },
    )
    assert result.data["transactions"][0]["transaction_id"] == "tx1"
    url = str(route.calls[0].request.url)
    assert "wallet_id=wallet-1" in url
    assert "flow=incoming" in url
    assert "asset_id=asset-btc" in url
    assert "from_including=2026-01-01" in url
    assert "to_excluding=2026-02-01" in url


async def test_list_transactions_all_bypasses_default_limit(
    mcp_client, mock_router: respx.MockRouter
) -> None:
    records = [_transaction(f"tx{i}", "deposit") for i in range(30)]
    mock_router.get("/v1/transactions").respond(json=_page(records, page_size=30))

    result = await mcp_client.call_tool("list_transactions", {"all": True})

    assert result.data["count"] == 30
    assert result.data["transactions"][-1]["transaction_id"] == "tx29"


async def test_list_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_transactions", {})


async def test_list_transactions_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_transactions = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Page", [{"type": "missing", "loc": ("data",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_transactions(ctx)
