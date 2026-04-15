from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_transactions(
    ctx: Context,
    wallet_id: str | None = None,
    flow: str | None = None,
    asset_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List your Bitpanda transactions with optional filters.

    Filters: wallet_id, flow (INCOMING/OUTGOING), asset_id, from_date, to_date.
    """
    try:
        txns = await get_bp_client(ctx).list_transactions(
            wallet_id=wallet_id,
            flow=flow,
            asset_id=asset_id,
            from_date=from_date,
            to_date=to_date,
            page_size=page_size,
            limit=limit,
        )
        return {"count": len(txns), "transactions": [t.model_dump(mode="json") for t in txns]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e


async def list_fiat_transactions(
    ctx: Context,
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List your fiat wallet transactions (deposits, withdrawals, payments)."""
    try:
        items = await get_bp_client(ctx).list_fiat_transactions(page_size=page_size, limit=limit)
        return {"count": len(items), "fiat_transactions": items}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e


async def list_crypto_transactions(
    ctx: Context,
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List your crypto wallet transactions (deposits, withdrawals, transfers)."""
    try:
        items = await get_bp_client(ctx).list_crypto_transactions(page_size=page_size, limit=limit)
        return {"count": len(items), "crypto_transactions": items}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
