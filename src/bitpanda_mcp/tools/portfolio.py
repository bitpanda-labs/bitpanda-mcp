from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_portfolio(
    ctx: Context,
    sort_by: str = "value",
) -> dict:
    """Get an aggregated portfolio view with current EUR valuations.

    Returns each held asset with balance, price, and EUR value. Sorted by 'value' (default) or 'name'.
    """
    try:
        wallets = await get_bp_client(ctx).list_wallets()
        ticker = await get_bp_client(ctx).fetch_ticker()

        # Aggregate balances by asset_id (multiple wallets can hold the same asset)
        balances: dict[str, float] = {}
        for w in wallets:
            if w.balance > 0:
                balances[w.asset_id] = balances.get(w.asset_id, 0.0) + w.balance

        holdings = []
        skipped_asset_ids: list[str] = []
        total_eur = 0.0

        for asset_id, balance in balances.items():
            entry = ticker.get_by_id(asset_id)
            if not entry:
                skipped_asset_ids.append(asset_id)
                continue

            try:
                price = float(entry.price)
            except (ValueError, TypeError):
                price = 0.0

            eur_value = balance * price
            total_eur += eur_value

            holdings.append(
                {
                    "asset_id": asset_id,
                    "name": entry.name,
                    "symbol": entry.symbol,
                    "type": entry.type,
                    "balance": balance,
                    "price_eur": entry.price,
                    "value_eur": round(eur_value, 2),
                }
            )

        if sort_by == "name":
            holdings.sort(key=lambda h: h["name"].lower())
        else:
            holdings.sort(key=lambda h: h["value_eur"], reverse=True)

        result: dict = {
            "count": len(holdings),
            "total_value_eur": round(total_eur, 2),
            "holdings": holdings,
        }
        if skipped_asset_ids:
            result["skipped_asset_ids"] = skipped_asset_ids
        return result
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
