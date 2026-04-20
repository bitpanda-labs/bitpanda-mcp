from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def list_fiat_transactions(
    ctx: Context,
    status: str | None = None,
    page_size: int = 25,
    limit: int = 100,
) -> dict:
    """List fiat wallet transactions (deposits, withdrawals, payments).

    Optional filter: ``status`` (e.g. ``finished``, ``pending``).
    """
    try:
        items = await get_bp_client(ctx).list_fiat_transactions(
            status=status, page_size=page_size, limit=limit
        )
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
    """List crypto wallet transactions (deposits, withdrawals, transfers)."""
    try:
        items = await get_bp_client(ctx).list_crypto_transactions(page_size=page_size, limit=limit)
        return {"count": len(items), "crypto_transactions": items}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
