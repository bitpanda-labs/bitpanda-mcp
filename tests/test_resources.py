import pytest
import respx
from mcp.shared.exceptions import McpError


async def test_asset_catalog(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets").respond(
        json={
            "data": [
                {"id": "a1", "name": "Bitcoin", "symbol": "BTC"},
                {"id": "a2", "name": "Ethereum", "symbol": "ETH"},
            ],
            "has_next_page": False,
            "page_size": 100,
        }
    )

    result = await mcp_client.read_resource("bitpanda://assets/catalog")
    text = result[0].text
    assert "id | name | symbol" in text
    assert "a1 | Bitcoin | BTC" in text
    assert "a2 | Ethereum | ETH" in text


async def test_asset_catalog_invalid_response(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets").respond(json={"not_data": True})
    with pytest.raises(McpError):
        await mcp_client.read_resource("bitpanda://assets/catalog")


async def test_asset_catalog_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/assets").respond(status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(McpError, match="Unauthorized"):
        await mcp_client.read_resource("bitpanda://assets/catalog")
