from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.models.wallets import Wallet
from bitpanda_mcp.tools.wallets import list_fiat_wallets, list_wallets


def _wallet_record(wid: str, symbol: str, balance: str) -> dict:
    return {
        "type": "wallet",
        "id": wid,
        "attributes": {
            "cryptocoin_id": "1",
            "cryptocoin_symbol": symbol,
            "balance": balance,
            "is_default": True,
            "name": f"{symbol} Wallet",
            "pending_transactions_count": 0,
            "deleted": False,
            "is_index": False,
        },
    }


WALLETS_RESPONSE = {
    "data": [
        _wallet_record("w1", "BTC", "0.05"),
        _wallet_record("w2", "ETH", "0.00"),
    ],
    "last_user_action": {"date_iso8601": "2026-04-20T10:00:00+02:00", "unix": "1776675000"},
}


def _fiat_record(fid: str, symbol: str, balance: str) -> dict:
    return {
        "type": "fiat_wallet",
        "id": fid,
        "attributes": {
            "fiat_id": "1",
            "fiat_symbol": symbol,
            "balance": balance,
            "name": f"{symbol} Wallet",
            "pending_transactions_count": 0,
        },
    }


async def test_list_wallets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(json=WALLETS_RESPONSE)

    result = await mcp_client.call_tool("list_wallets", {})
    assert result.data["count"] == 2
    wallets = result.data["wallets"]
    assert wallets[0]["id"] == "w1"
    assert wallets[0]["cryptocoin_symbol"] == "BTC"
    assert wallets[0]["balance"] == "0.05"


async def test_list_wallets_non_zero(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(json=WALLETS_RESPONSE)

    result = await mcp_client.call_tool("list_wallets", {"non_zero": True})
    assert result.data["count"] == 1
    assert result.data["wallets"][0]["cryptocoin_symbol"] == "BTC"


async def test_list_wallets_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(status_code=401, json={"message": "Bad key"})

    with pytest.raises(ToolError, match="Bad key"):
        await mcp_client.call_tool("list_wallets", {})


async def test_list_wallets_empty_data(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(json={"data": []})

    result = await mcp_client.call_tool("list_wallets", {})
    assert result.data == {"count": 0, "wallets": []}


async def test_list_fiat_wallets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets").respond(json={"data": [_fiat_record("fw1", "EUR", "1500.00")]})

    result = await mcp_client.call_tool("list_fiat_wallets", {})
    assert result.data["count"] == 1
    fw = result.data["fiat_wallets"][0]
    assert fw["id"] == "fw1"
    assert fw["fiat_symbol"] == "EUR"
    assert fw["balance"] == "1500.00"


async def test_list_fiat_wallets_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets").respond(status_code=500, json={"message": "Server error"})
    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("list_fiat_wallets", {})


async def test_list_fiat_wallets_validation_error_direct() -> None:
    """Call tool directly (not via MCP) to cover except ValidationError."""
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_fiat_wallets = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "FiatWallet", [{"type": "missing", "loc": ("id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with pytest.raises(ToolError, match="Unexpected API response"):
        await list_fiat_wallets(ctx)


async def test_list_wallets_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_wallets = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Wallet", [{"type": "missing", "loc": ("id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.wallets.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await list_wallets(ctx)


def test_wallet_balance_float_non_numeric() -> None:
    w = Wallet(id="w1", balance="not-a-number")
    assert w.balance_float == 0.0
