from typing import TYPE_CHECKING

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError

if TYPE_CHECKING:
    from bitpanda_mcp.models.market import Ticker
    from bitpanda_mcp.models.wallets import Wallet


def _collect_balances(wallets: list["Wallet"]) -> dict[str, float]:
    balances: dict[str, float] = {}
    for w in wallets:
        bal = w.balance_float
        if bal <= 0:
            continue
        key = w.cryptocoin_symbol.upper()
        if not key:
            continue
        balances[key] = balances.get(key, 0.0) + bal
    return balances


def _build_holdings(balances: dict[str, float], ticker: "Ticker") -> tuple[list[dict], list[str], float]:
    holdings: list[dict] = []
    skipped: list[str] = []
    total_eur = 0.0
    for symbol, balance in balances.items():
        entry = ticker.get_by_symbol(symbol)
        if not entry:
            skipped.append(symbol)
            continue
        try:
            price = float(entry.price_eur)
        except (ValueError, TypeError):
            price = 0.0
        eur_value = balance * price
        total_eur += eur_value
        holdings.append(
            {
                "symbol": symbol,
                "balance": balance,
                "price_eur": entry.price_eur,
                "value_eur": round(eur_value, 2),
            }
        )
    return holdings, skipped, total_eur


async def get_portfolio(ctx: Context, sort_by: str = "value") -> dict:
    """Get an aggregated portfolio view with current EUR valuations.

    Returns each held asset with balance, price, and EUR value. Sorted by
    ``value`` (default) or ``name``.
    """
    try:
        client = get_bp_client(ctx)
        wallets = await client.list_wallets()
        ticker = await client.fetch_ticker()

        balances = _collect_balances(wallets)
        holdings, skipped_symbols, total_eur = _build_holdings(balances, ticker)

        if sort_by == "name":
            holdings.sort(key=lambda h: h["symbol"])
        else:
            holdings.sort(key=lambda h: h["value_eur"], reverse=True)

        result: dict = {
            "count": len(holdings),
            "total_value_eur": round(total_eur, 2),
            "holdings": holdings,
        }
        if skipped_symbols:
            result["skipped_symbols"] = skipped_symbols
        return result
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
