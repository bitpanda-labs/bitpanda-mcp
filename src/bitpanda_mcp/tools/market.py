from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_price(ctx: Context, symbol: str) -> dict:
    """Get the current EUR price for an asset by its symbol (e.g. BTC, ETH)."""
    try:
        ticker = await get_bp_client(ctx).fetch_ticker()
        entry = ticker.get_by_symbol(symbol)
        if not entry:
            raise ToolError(f"No price data found for symbol '{symbol}'")
        return {"symbol": entry.symbol, "price_eur": entry.price_eur}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
