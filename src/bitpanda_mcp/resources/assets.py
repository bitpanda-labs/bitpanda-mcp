from fastmcp import Context
from fastmcp.exceptions import ResourceError
from pydantic import ValidationError

from bitpanda_mcp.clients import get_bp_client
from bitpanda_mcp.models.common import BitpandaAPIError


async def get_asset_catalog(ctx: Context) -> str:
    """Full catalog of available assets on Bitpanda with IDs, names, and symbols."""
    try:
        items = await get_bp_client(ctx).list_assets(page_size=100, limit=0)
        lines = ["id | name | symbol"]
        lines.append("--- | --- | ---")
        for item in items:
            lines.append(f"{item.get('id', '')} | {item.get('name', '')} | {item.get('symbol', '')}")
        return "\n".join(lines)
    except BitpandaAPIError as e:
        raise ResourceError(e.detail) from e
    except ValidationError as e:
        raise ResourceError(f"Unexpected API response: {e}") from e
