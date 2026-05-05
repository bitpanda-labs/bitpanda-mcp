from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_asset(ctx: Context, asset_id: str) -> dict:
    """Get asset metadata by asset UUID."""
    try:
        asset = await get_bp_client(ctx).get_asset(asset_id)
        return {"asset": asset.model_dump(mode="json")}
    except BitpandaAPIError as e:
        raise ToolError(e.detail) from e
    except ValidationError as e:
        raise ToolError(f"Unexpected API response: {e}") from e
