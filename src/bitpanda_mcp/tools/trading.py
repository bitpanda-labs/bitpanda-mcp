from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_trades(
    ctx: Context,
    trade_type: str | None = None,
    operation: str | None = None,
    asset_type: str | None = None,
    from_including: str | None = None,
    to_excluding: str | None = None,
    all: bool = False,  # noqa: A002
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List your buy/sell trades on Bitpanda.

    Optional filters: ``trade_type``/``operation`` (buy/sell), ``asset_type``, and date range.
    """
    try:
        if trade_type and operation and trade_type != operation:
            raise ToolError("Conflicting values provided for 'trade_type' and 'operation'.")
        fetch_limit = 0 if all else limit
        effective_trade_type = trade_type or operation
        trades = await get_bp_client(ctx).list_trades(
            trade_type=effective_trade_type,
            asset_type=asset_type,
            from_including=from_including,
            to_excluding=to_excluding,
            page_size=page_size,
            limit=fetch_limit,
        )
        return {"count": len(trades), "trades": [t.model_dump(mode="json") for t in trades]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
