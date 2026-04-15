from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.assets import AssetData
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_asset(asset_id: str, ctx: Context) -> AssetData:
    """Look up asset metadata (name, symbol) by its UUID."""
    try:
        return await get_bp_client(ctx).get_asset(asset_id)
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e


async def list_assets(
    ctx: Context,
    asset_type: str | None = None,
    page_size: int = 25,
    limit: int = 0,
) -> dict:
    """List available assets on Bitpanda.

    Optional filter: asset_type (cryptocoin, metal, stock, etf).
    """
    try:
        items = await get_bp_client(ctx).list_assets(asset_type=asset_type, page_size=page_size, limit=limit)
        return {"count": len(items), "assets": items}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
