from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_trades(
    ctx: Context,
    trade_type: str | None = None,
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List your buy/sell trades on Bitpanda.

    Optional filter: ``trade_type`` (buy/sell).
    """
    try:
        trades = await get_bp_client(ctx).list_trades(trade_type=trade_type, page_size=page_size, limit=limit)
        return {"count": len(trades), "trades": [t.model_dump(mode="json") for t in trades]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
