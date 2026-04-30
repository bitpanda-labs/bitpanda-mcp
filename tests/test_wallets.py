from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bitpanda_mcp.models.wallets import Wallet
from bitpanda_mcp.tools.wallets import list_wallets


def _wallet_record(wid: str, asset_id: str, balance: str, wallet_type: str = "") -> dict:
    return {
        "wallet_id": wid,
        "asset_id": asset_id,
        "wallet_type": wallet_type,
        "index_asset_id": "",
        "last_credited_at": "2026-04-20T10:00:00Z",
        "balance": balance,
    }


WALLETS_RESPONSE = {
    "data": [
        _wallet_record("w1", "asset-btc", "0.05"),
        _wallet_record("w2", "asset-eth", "0.00"),
    ],
    "has_next_page": False,
}


async def test_list_wallets(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json=WALLETS_RESPONSE)

    result = await mcp_client.call_tool("list_wallets", {})
    assert result.data["count"] == 2
    wallets = result.data["wallets"]
    assert wallets[0]["wallet_id"] == "w1"
    assert wallets[0]["asset_id"] == "asset-btc"
    assert wallets[0]["balance"] == "0.05"


async def test_list_wallets_non_zero(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json=WALLETS_RESPONSE)

    result = await mcp_client.call_tool("list_wallets", {"non_zero": True})
    assert result.data["count"] == 1
    assert result.data["wallets"][0]["asset_id"] == "asset-btc"


async def test_list_wallets_filters(mcp_client, mock_router: respx.MockRouter) -> None:
    route = mock_router.get("/v1/wallets/").respond(json={"data": [_wallet_record("w1", "asset-btc", "1")]})

    result = await mcp_client.call_tool(
        "list_wallets", {"asset_id": "asset-btc", "page_size": 50, "limit": 1}
    )
    assert result.data["count"] == 1
    url = str(route.calls[0].request.url)
    assert "asset_id=asset-btc" in url
    assert "page_size=50" in url


async def test_list_wallets_error(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(status_code=401, json={"message": "Bad key"})

    with pytest.raises(ToolError, match="Bad key"):
        await mcp_client.call_tool("list_wallets", {})


async def test_list_wallets_empty_data(mcp_client, mock_router: respx.MockRouter) -> None:
    mock_router.get("/v1/wallets/").respond(json={"data": [], "has_next_page": False})

    result = await mcp_client.call_tool("list_wallets", {})
    assert result.data == {"count": 0, "wallets": []}


async def test_list_wallets_validation_error_direct() -> None:
    ctx = MagicMock()
    bp = MagicMock()
    bp.list_wallets = AsyncMock(
        side_effect=ValidationError.from_exception_data(
            "Wallet", [{"type": "missing", "loc": ("wallet_id",), "msg": "missing", "input": {}}]
        )
    )
    ctx.lifespan_context = {"bp": bp}
    with (
        patch("bitpanda_mcp.tools.wallets.get_bp_client", return_value=bp),
        pytest.raises(ToolError, match="Unexpected API response"),
    ):
        await list_wallets(ctx)


def test_wallet_balance_float_non_numeric() -> None:
    w = Wallet(wallet_id="w1", balance="not-a-number")
    assert w.balance_float == 0.0


def test_wallet_effective_wallet_type() -> None:
    assert Wallet(wallet_id="w1", wallet_type="", balance="1").effective_wallet_type == "regular"
    assert Wallet(wallet_id="w2", wallet_type="STAKING", balance="1").effective_wallet_type == "STAKING"
