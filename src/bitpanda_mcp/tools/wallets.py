from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_wallets(
    ctx: Context,
    asset_id: str | None = None,
    non_zero: bool = False,
    page_size: int = 25,
) -> dict:
    """List your Bitpanda crypto wallet balances. Set non_zero=true to hide empty wallets."""
    try:
        wallets = await get_bp_client(ctx).list_wallets(asset_id=asset_id, page_size=page_size)
        items = [w.model_dump(mode="json") for w in wallets]
        if non_zero:
            items = [w for w in items if w["balance"] > 0]
        return {"count": len(items), "wallets": items}
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
