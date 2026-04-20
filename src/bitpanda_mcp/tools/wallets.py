from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_wallets(ctx: Context, non_zero: bool = False) -> dict:
    """List your Bitpanda crypto wallet balances.

    Set ``non_zero=true`` to hide wallets with a zero balance.
    """
    try:
        wallets = await get_bp_client(ctx).list_wallets()
        if non_zero:
            wallets = [w for w in wallets if w.balance_float > 0]
        return {"count": len(wallets), "wallets": [w.model_dump() for w in wallets]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e


async def list_fiat_wallets(ctx: Context) -> dict:
    """List your fiat currency wallets (EUR, USD, GBP, CHF) with balances."""
    try:
        wallets = await get_bp_client(ctx).list_fiat_wallets()
        return {"count": len(wallets), "fiat_wallets": [w.model_dump() for w in wallets]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
