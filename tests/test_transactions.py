from unittest.mock import AsyncMock, MagicMock

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.tools.transactions import list_crypto_transactions, list_fiat_transactions


def _fiat_tx(tid: str, tx_type: str) -> dict:
    return {
        "type": "fiat_wallet_transaction",
        "id": tid,
        "attributes": {
            "fiat_wallet_id": "fw1",
            "fiat_id": "1",
            "amount": "500.00",
            "fee": "0.00",
            "type": tx_type,
            "status": "finished",
            "in_or_out": "incoming",
        },
    }


def _crypto_tx(tid: str, tx_type: str) -> dict:
    return {
        "type": "wallet_transaction",
        "id": tid,
        "attributes": {
            "amount": "0.1",
            "wallet_id": "w1",
            "cryptocoin_id": "1",
            "cryptocoin_symbol": "BTC",
            "fee": "0.00000000",
            "type": tx_type,
            "status": "finished",
            "in_or_out": "incoming",
        },
    }


def _page(records: list[dict], total: int, page_size: int = 25, page_number: int = 1) -> dict:
    return {
        "data": records,
        "meta": {
            "total_count": total,
            "page_size": page_size,
            "page": page_number,
            "page_number": page_number,
        },
        "links": {"self": f"?page_number={page_number}&page_size={page_size}"},
    }


async def test_list_fiat_transactions(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(json=_page([_fiat_tx("ft1", "deposit")], 1))

    result = await mcp_client.call_tool("list_fiat_transactions", {})
    assert result.data["count"] == 1
    tx = result.data["fiat_transactions"][0]
    assert tx["id"] == "ft1"
    assert tx["type"] == "deposit"


async def test_list_fiat_transactions_with_status_filter(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    route = mock_router.get("/v1/fiatwallets/transactions").respond(json=_page([], 0))
    items = await bp_client.list_fiat_transactions(status="finished")
    assert items == []
    assert "status=finished" in str(route.calls[0].request.url)


async def test_list_crypto_transactions(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/transactions").respond(json=_page([_crypto_tx("ct1", "deposit")], 1))

    result = await mcp_client.call_tool("list_crypto_transactions", {})
    assert result.data["count"] == 1
    tx = result.data["crypto_transactions"][0]
    assert tx["id"] == "ct1"
    assert tx["cryptocoin_symbol"] == "BTC"


async def test_list_fiat_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_fiat_transactions", {})


async def test_list_crypto_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/transactions").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_crypto_transactions", {})


async def test_list_fiat_transactions_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_fiat_transactions = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Page", [{"type": "missing", "loc": ("data",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_fiat_transactions(ctx)


async def test_list_crypto_transactions_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_crypto_transactions = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Page", [{"type": "missing", "loc": ("data",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_crypto_transactions(ctx)
