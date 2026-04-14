import pytest
import respx
from fastmcp.exceptions import ToolError


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
