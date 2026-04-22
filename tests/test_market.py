from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.tools.market import get_price

TICKER_FLAT = {
    "BTC": {"EUR": "65000.00", "USD": "75000.00"},
    "ETH": {"EUR": "3500.00", "USD": "4000.00"},
    "XAU": {"EUR": "131.00"},
    "NOPRICE": {"USD": "1.00"},  # no EUR — should be skipped
}


async def test_get_price(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    result = await mcp_client.call_tool("get_price", {"symbol": "BTC"})
    assert result.data["symbol"] == "BTC"
    assert result.data["price_eur"] == "65000.00"


async def test_get_price_case_insensitive(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    result = await mcp_client.call_tool("get_price", {"symbol": "btc"})
    assert result.data["symbol"] == "BTC"


async def test_get_price_not_found(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    with pytest.raises(ToolError, match="DOGE"):
        await mcp_client.call_tool("get_price", {"symbol": "DOGE"})


async def test_get_price_skips_symbols_without_eur(mcp_client, mock_router: respx.MockRouter) -> None:
    """Ticker symbols that don't quote EUR are treated as not found."""
    mock_router.get("/v1/ticker").respond(json=TICKER_FLAT)

    with pytest.raises(ToolError, match="NOPRICE"):
        await mcp_client.call_tool("get_price", {"symbol": "NOPRICE"})


async def test_get_price_non_dict_response(mcp_client, mock_router: respx.MockRouter) -> None:
    """If the ticker returns something other than a dict, we treat it as empty."""
    mock_router.get("/v1/ticker").respond(json=[])

    with pytest.raises(ToolError, match="BTC"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_api_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/ticker").respond(status_code=500, json={"message": "Server error"})

    with pytest.raises(ToolError, match="Server error"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_skips_non_dict_price_entries(mcp_client, mock_router: respx.MockRouter) -> None:
    """Symbols whose prices map is not a dict (e.g. string) are silently skipped."""
    mock_router.get("/v1/ticker").respond(json={"BTC": "65000.00", "ETH": {"EUR": "3500.00"}})

    result = await mcp_client.call_tool("get_price", {"symbol": "ETH"})
    assert result.data["price_eur"] == "3500.00"

    with pytest.raises(ToolError, match="BTC"):
        await mcp_client.call_tool("get_price", {"symbol": "BTC"})


async def test_get_price_validation_error_direct() -> None:
    """Direct call covers ``except ValidationError`` in get_price."""
    ctx = MagicMock()
    bp = MagicMock()
    bp.fetch_ticker = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "TickerEntry", [{"type": "missing", "loc": ("symbol",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.market.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await get_price(ctx, "BTC")
