import httpx
import pytest
import respx
from fastmcp.exceptions import ToolError


def _wallet_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "data": [
                {
                    "wallet_id": "w1",
                    "asset_id": "a1",
                    "wallet_type": None,
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-01T00:00:00Z",
                    "balance": 1.5,
                },
                {
                    "wallet_id": "w2",
                    "asset_id": "a2",
                    "wallet_type": "STAKING",
                    "index_asset_id": None,
                    "last_credited_at": "2025-01-02T00:00:00Z",
                    "balance": 0.0,
                },
            ],
            "has_next_page": False,
            "page_size": 25,
        },
    )


async def test_list_wallets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").mock(side_effect=_wallet_handler)

    result = await mcp_client.call_tool("list_wallets", {})
    assert result.data["count"] == 2
    assert result.data["wallets"][0]["wallet_id"] == "w1"


async def test_list_wallets_non_zero(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").mock(side_effect=_wallet_handler)

    result = await mcp_client.call_tool("list_wallets", {"non_zero": True})
    assert result.data["count"] == 1
    assert result.data["wallets"][0]["balance"] == 1.5


async def test_list_wallets_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(status_code=401, json={"message": "Bad key"})

    with pytest.raises(ToolError, match="Bad key"):
        await mcp_client.call_tool("list_wallets", {})


async def test_list_fiat_wallets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/fiatwallets").respond(
        json={
            "data": [
                {
                    "id": "fw1",
                    "type": "fiat",
                    "fiat_id": "f-eur",
                    "fiat_symbol": "EUR",
                    "balance": "1500.00",
                    "name": "EUR Wallet",
                },
            ],
        }
    )

    result = await mcp_client.call_tool("list_fiat_wallets", {})
    assert result.data["count"] == 1
    assert result.data["fiat_wallets"][0]["fiat_symbol"] == "EUR"
    assert result.data["fiat_wallets"][0]["balance"] == "1500.00"
