import httpx
import pytest
import respx
from fastmcp.exceptions import ToolError

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.models.common import BitpandaAPIError

SAMPLE_ASSET = {
    "data": {
        "id": "abc-123",
        "name": "Bitcoin",
        "symbol": "BTC",
        "extra_field": "ignored",
    }
}


def _paginated_asset_handler(request: httpx.Request) -> httpx.Response:
    """Return page 1 or page 2 depending on the cursor param."""
    params = dict(request.url.params)
    if params.get("after") == "cursor-1":
        return httpx.Response(
            200,
            json={
                "data": [{"id": "ghi-789", "name": "Solana", "symbol": "SOL"}],
                "has_next_page": False,
                "end_cursor": None,
                "page_size": 2,
            },
        )
    return httpx.Response(
        200,
        json={
            "data": [
                {"id": "abc-123", "name": "Bitcoin", "symbol": "BTC"},
                {"id": "def-456", "name": "Ethereum", "symbol": "ETH"},
            ],
            "has_next_page": True,
            "end_cursor": "cursor-1",
            "page_size": 2,
        },
    )


# --- Client-level tests ---


async def test_get_asset(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/abc-123").respond(json=SAMPLE_ASSET)

    asset = await bp_client.get_asset("abc-123")
    assert asset.id == "abc-123"
    assert asset.name == "Bitcoin"
    assert asset.symbol == "BTC"


async def test_get_asset_not_found(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/bad-id").respond(
        status_code=404,
        json={"errors": [{"title": "Not Found"}]},
    )

    with pytest.raises(BitpandaAPIError, match="Not Found"):
        await bp_client.get_asset("bad-id")


async def test_list_assets_pagination(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets").mock(side_effect=_paginated_asset_handler)

    items = await bp_client.list_assets(page_size=2)
    assert len(items) == 3
    assert items[0]["symbol"] == "BTC"
    assert items[2]["symbol"] == "SOL"


async def test_list_assets_with_limit(bp_client: BitpandaClient, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets").mock(side_effect=_paginated_asset_handler)

    items = await bp_client.list_assets(page_size=2, limit=1)
    assert len(items) == 1


# --- MCP tool-level tests ---


async def test_mcp_get_asset(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/abc-123").respond(json=SAMPLE_ASSET)

    result = await mcp_client.call_tool("get_asset", {"asset_id": "abc-123"})
    assert result.data.id == "abc-123"
    assert result.data.symbol == "BTC"


async def test_mcp_get_asset_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets/bad").respond(status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(ToolError, match="Unauthorized"):
        await mcp_client.call_tool("get_asset", {"asset_id": "bad"})


async def test_mcp_list_assets(mcp_client, mock_router: respx.MockRouter) -> None:
    page = {
        "data": [{"id": "1", "name": "Bitcoin", "symbol": "BTC"}],
        "has_next_page": False,
        "page_size": 25,
    }
    mock_router.get("/v1/assets").respond(json=page)

    result = await mcp_client.call_tool("list_assets", {})
    assert result.data["count"] == 1
    assert result.data["assets"][0]["symbol"] == "BTC"
