from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_wallets(
    ctx: Context,
    non_zero: bool = False,
    asset_id: str | None = None,
    page_size: int = 25,
    limit: int = 0,
) -> dict:
    """List your Bitpanda asset wallet balances.

    Set ``non_zero=true`` to hide wallets with a zero balance. Use ``asset_id``
    to filter by asset UUID.
    """
    try:
        wallets = await get_bp_client(ctx).list_wallets(asset_id=asset_id, page_size=page_size, limit=limit)
        if non_zero:
            wallets = [w for w in wallets if w.balance_float > 0]
        return {"count": len(wallets), "wallets": [w.model_dump(mode="json") for w in wallets]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
