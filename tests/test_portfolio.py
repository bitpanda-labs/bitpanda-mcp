from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.tools.portfolio import get_portfolio


def _wallet(wid: str, symbol: str, balance: str) -> dict:
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
        _wallet("w1", "BTC", "0.5"),
        _wallet("w2", "ETH", "2.0"),
        _wallet("w3", "DOGE", "0.0"),
        _wallet("w4", "UNKNOWN", "100.0"),
    ],
    "last_user_action": {"date_iso8601": "2026-04-20T10:00:00+02:00", "unix": "1776675000"},
}

TICKER_FLAT = {
    "BTC": {"EUR": "65000.00"},
    "ETH": {"EUR": "3500.00"},
    "DOGE": {"EUR": "0.10"},
}


async def test_get_portfolio(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(json=WALLETS_RESPONSE)
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    result = await mcp_client.call_tool("get_portfolio", {})
    data = result.data
    assert data["count"] == 2
    assert data["total_value_eur"] == 39500.0

    # Default sort by value desc: BTC (32500) > ETH (7000)
    assert data["holdings"][0]["symbol"] == "BTC"
    assert data["holdings"][0]["value_eur"] == 32500.0
    assert data["holdings"][1]["symbol"] == "ETH"
    assert data["holdings"][1]["value_eur"] == 7000.0

    # UNKNOWN has a balance but no ticker entry — surfaced, not silently dropped
    assert data["skipped_symbols"] == ["UNKNOWN"]


async def test_get_portfolio_sort_by_name(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(json=WALLETS_RESPONSE)
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    result = await mcp_client.call_tool("get_portfolio", {"sort_by": "name"})
    holdings = result.data["holdings"]
    assert [h["symbol"] for h in holdings] == ["BTC", "ETH"]


async def test_get_portfolio_non_numeric_price(mcp_client, mock_router: respx.MockRouter) -> None:
    """Non-numeric ticker price falls back to 0."""
    mock_router.get("/v1/wallets").respond(
        json={"data": [_wallet("w1", "BRK", "10.0")], "last_user_action": {}}
    )
    mock_router.get("/v1/ticker").respond(json={"BRK": {"EUR": "not-a-number"}})

    result = await mcp_client.call_tool("get_portfolio", {})
    assert result.data["holdings"][0]["value_eur"] == 0.0


async def test_get_portfolio_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets").respond(status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(ToolError, match="Unauthorized"):
        await mcp_client.call_tool("get_portfolio", {})


async def test_get_portfolio_skips_wallet_without_symbol(mcp_client, mock_router: respx.MockRouter) -> None:
    """A wallet whose cryptocoin_symbol is empty is skipped from the portfolio aggregation."""
    empty_symbol_wallet = _wallet("w1", "", "1.0")
    mock_router.get("/v1/wallets").respond(json={"data": [empty_symbol_wallet, _wallet("w2", "BTC", "0.5")]})
    mock_router.get("/v1/ticker").respond(json={"BTC": {"EUR": "65000.00"}})

    result = await mcp_client.call_tool("get_portfolio", {})
    # Only BTC should appear; the symbol-less wallet is skipped silently.
    assert [h["symbol"] for h in result.data["holdings"]] == ["BTC"]


async def test_get_portfolio_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_wallets = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Wallet", [{"type": "missing", "loc": ("id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.portfolio.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await get_portfolio(ctx)
