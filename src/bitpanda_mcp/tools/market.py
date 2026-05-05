from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_price(ctx: Context, symbol: str) -> dict:
    """Get the current price for an asset by its symbol (e.g. BTC, ETH)."""
    try:
        ticker = await get_bp_client(ctx).fetch_ticker()
        entry = ticker.get_by_symbol(symbol)
        if not entry:
            raise ToolError(f"No price data found for symbol '{symbol}'")
        return {
            "symbol": entry.symbol,
            "name": entry.name,
            "asset_id": entry.id,
            "type": entry.type,
            "currency": entry.currency,
            "price": entry.price,
            "price_eur": entry.price_eur,
            "price_change_day": entry.price_change_day,
        }
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e


async def list_prices(
    ctx: Context,
    all_assets: bool = False,
    all: bool = False,  # noqa: A002
    limit: int = 100,
) -> dict:
    """List ticker prices.

    By default, returns held assets that have ticker data. Set ``all_assets``/``all``
    to include the market-wide ticker list. ``limit`` caps returned rows; use
    ``limit=0`` for no cap.
    """
    try:
        client = get_bp_client(ctx)
        ticker = await client.fetch_ticker()

        entries = ticker.entries
        skipped_asset_ids: list[str] = []
        if not (all_assets or all):
            wallets = await client.list_wallets(page_size=100)
            held_asset_ids = {
                wallet.asset_id.strip()
                for wallet in wallets
                if wallet.balance_float > 0 and wallet.asset_id and wallet.asset_id.strip()
            }
            entries = [entry for entry in entries if entry.id in held_asset_ids]
            skipped_asset_ids = sorted(held_asset_ids - {entry.id for entry in entries})

        prices = [
            {
                "asset_id": entry.id,
                "symbol": entry.symbol,
                "name": entry.name,
                "type": entry.type,
                "currency": entry.currency,
                "price": entry.price,
                "price_eur": entry.price_eur,
                "price_change_day": entry.price_change_day,
            }
            for entry in entries
        ]
        prices.sort(key=lambda item: item["symbol"])
        total_available = len(prices)
        if limit > 0:
            prices = prices[:limit]

        result: dict = {"count": len(prices), "total_available": total_available, "prices": prices}
        if skipped_asset_ids:
            result["skipped_asset_ids"] = skipped_asset_ids
        return result
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
