from fastmcp import Context
from fastmcp.exceptions import ToolError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_price(symbol: str, ctx: Context) -> dict:
    """Get the current price and 24h change for an asset by its symbol (e.g. BTC, ETH, BEST)."""
    try:
        ticker = await get_bp_client(ctx).fetch_ticker()
        entry = ticker.get_by_symbol(symbol)
        if not entry:
            raise ToolError(f"No price data found for symbol '{symbol}'")
        return {
            "symbol": entry.symbol,
            "name": entry.name,
            "price_eur": entry.price,
            "change_24h": entry.price_change_day,
            "type": entry.type,
        }
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
