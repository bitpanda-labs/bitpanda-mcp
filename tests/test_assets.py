from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.tools.assets import get_asset

ASSET = {"id": "asset-btc", "name": "Bitcoin", "symbol": "BTC"}


async def test_get_asset(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/asset-btc").respond(json={"data": ASSET})

    result = await mcp_client.call_tool("get_asset", {"asset_id": "asset-btc"})
    assert result.data["asset"] == ASSET


async def test_get_asset_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/missing").respond(status_code=404, json={"message": "Not found"})

    with pytest.raises(ToolError, match="Not found"):
        await mcp_client.call_tool("get_asset", {"asset_id": "missing"})


async def test_get_asset_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.get_asset = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Asset", [{"type": "missing", "loc": ("id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.assets.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await get_asset(ctx, "asset-btc")
