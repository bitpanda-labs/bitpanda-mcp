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
    from_including: str | None = None,
    to_excluding: str | None = None,
    all: bool = False,  # noqa: A002 - keep MCP argument aligned with bitpanda-cli
    page_size: int = 25,
    limit: int = 25,
) -> dict:
    """List asset transactions with optional wallet, flow, asset, and date filters."""
    try:
        fetch_limit = 0 if all else limit
        items = await get_bp_client(ctx).list_transactions(
            wallet_id=wallet_id,
            flow=flow,
            asset_id=asset_id,
            from_including=from_including,
            to_excluding=to_excluding,
            page_size=page_size,
            limit=fetch_limit,
        )
        return {"count": len(items), "transactions": [item.model_dump(mode="json") for item in items]}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
