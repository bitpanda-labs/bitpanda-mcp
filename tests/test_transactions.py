from unittest.mock import AsyncMock, MagicMock

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.tools.transactions import list_crypto_transactions, list_fiat_transactions


async def test_list_transactions(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(
        json={
            "data": [
                {
                    "transaction_id": "t1",
                    "operation_id": "op1",
                    "asset_id": "a1",
                    "account_id": "acc1",
                    "wallet_id": "w1",
                    "asset_amount": 0.5,
                    "fee_amount": 0.001,
                    "operation_type": "buy",
                    "flow": "INCOMING",
                    "credited_at": "2025-03-15T10:00:00Z",
                    "trade_id": "tr1",
                },
            ],
            "has_next_page": False,
            "page_size": 25,
        }
    )

    result = await mcp_client.call_tool("list_transactions", {})
    assert result.data["count"] == 1
    assert result.data["transactions"][0]["transaction_id"] == "t1"


async def test_list_transactions_with_filters(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/transactions").respond(json={"data": [], "has_next_page": False})
    txns = await bp_client.list_transactions(
        wallet_id="w1", flow="INCOMING", asset_id="a1", from_date="2025-01-01", to_date="2025-12-31"
    )
    assert txns == []


async def test_list_fiat_transactions_with_filters(
    bp_client: BitpandaClient, mock_router: respx.MockRouter
) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(
        json={"data": [{"id": "ft1"}], "has_next_page": False}
    )
    items = await bp_client.list_fiat_transactions(fiat_wallet_id="fw1", status="finished")
    assert len(items) == 1


async def test_list_transactions_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(json={"data": [{"bad": "shape"}], "has_next_page": False})
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("list_transactions", {})


async def test_list_fiat_transactions_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(json={"not_data": True})
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("list_fiat_transactions", {})


async def test_list_crypto_transactions_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/transactions").respond(json={"not_data": True})
    with pytest.raises(ToolError, match="Unexpected API response"):
        await mcp_client.call_tool("list_crypto_transactions", {})


async def test_list_fiat_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_fiat_transactions", {})


async def test_list_crypto_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/transactions").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_crypto_transactions", {})


async def test_list_fiat_transactions_validation_error_direct() -> None:
    """Call tool directly (not via MCP) to cover except ValidationError."""
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_fiat_transactions = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "CursorPage", [{"type": "missing", "loc": ("data",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_fiat_transactions(ctx)


async def test_list_crypto_transactions_validation_error_direct() -> None:
    """Call tool directly (not via MCP) to cover except ValidationError."""
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_crypto_transactions = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "CursorPage", [{"type": "missing", "loc": ("data",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_crypto_transactions(ctx)


async def test_list_transactions_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/transactions").respond(status_code=403, json={"message": "Forbidden"})

    with pytest.raises(ToolError, match="Forbidden"):
        await mcp_client.call_tool("list_transactions", {})


async def test_list_fiat_transactions(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets/transactions").respond(
        json={
            "data": [{"id": "ft1", "type": "deposit", "amount": "500.00", "fiat_id": "f-eur"}],
            "has_next_page": False,
            "page_size": 25,
        }
    )

    result = await mcp_client.call_tool("list_fiat_transactions", {})
    assert result.data["count"] == 1
    assert result.data["fiat_transactions"][0]["type"] == "deposit"


async def test_list_crypto_transactions(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/transactions").respond(
        json={
            "data": [{"id": "ct1", "type": "transfer", "amount": "0.1", "asset_id": "a-btc"}],
            "has_next_page": False,
            "page_size": 25,
        }
    )

    result = await mcp_client.call_tool("list_crypto_transactions", {})
    assert result.data["count"] == 1
    assert result.data["crypto_transactions"][0]["type"] == "transfer"
