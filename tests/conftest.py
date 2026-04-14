from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
import respx
from fastmcp import Client, FastMCP

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.prompts import portfolio as portfolio_prompts
from bitpanda_mcp.resources import assets as asset_resources
from bitpanda_mcp.tools import assets as asset_tools
from bitpanda_mcp.tools import market as market_tools
from bitpanda_mcp.tools import portfolio as portfolio_tools
from bitpanda_mcp.tools import trading as trading_tools
from bitpanda_mcp.tools import transactions as transaction_tools
from bitpanda_mcp.tools import wallets as wallet_tools


@pytest.fixture
def bp_base_url() -> str:
    return "https://test.bitpanda.com"


@pytest.fixture
def mock_router(bp_base_url: str) -> respx.MockRouter:
    """Create a respx mock router scoped to the Bitpanda base URL."""
    with respx.mock(base_url=bp_base_url) as router:
        yield router


@pytest.fixture
def bp_client(mock_router: respx.MockRouter, bp_base_url: str) -> BitpandaClient:
    """BitpandaClient wired to the mocked HTTP transport."""
    http = httpx.AsyncClient(base_url=bp_base_url)
    return BitpandaClient(http, api_key="test-key")


def _register_all(server: FastMCP) -> None:
    """Register all Bitpanda tools, resources, and prompts on the server."""
    server.tool()(asset_tools.get_asset)
    server.tool()(asset_tools.list_assets)
    server.tool()(wallet_tools.list_wallets)
    server.tool()(wallet_tools.list_fiat_wallets)
    server.tool()(transaction_tools.list_transactions)
    server.tool()(transaction_tools.list_fiat_transactions)
    server.tool()(transaction_tools.list_crypto_transactions)
    server.tool()(trading_tools.list_trades)
    server.tool()(market_tools.get_price)
    server.tool()(portfolio_tools.get_portfolio)
    server.resource("bitpanda://assets/catalog")(asset_resources.get_asset_catalog)
    server.prompt()(portfolio_prompts.portfolio_summary)
    server.prompt()(portfolio_prompts.recent_activity)


@pytest.fixture
def mcp_server(mock_router: respx.MockRouter, bp_base_url: str) -> FastMCP:
    """FastMCP server with mocked BitpandaClient (simulates stdio mode)."""
    http = httpx.AsyncClient(base_url=bp_base_url)
    bp = BitpandaClient(http, api_key="test-key")

    @asynccontextmanager
    async def test_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {"http": http, "bp": bp}
        finally:
            await http.aclose()

    server = FastMCP(name="test-server", lifespan=test_lifespan)
    _register_all(server)
    return server


@pytest.fixture
async def mcp_client(mcp_server: FastMCP) -> Client:
    """FastMCP test client."""
    async with Client(mcp_server) as client:
        yield client
