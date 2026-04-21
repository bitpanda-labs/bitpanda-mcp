from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
import respx
from fastmcp import Client, FastMCP

from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.server import register


@pytest.fixture
def bp_base_url() -> str:
    return "https://test.bitpanda.com"


@pytest.fixture
def mock_router(bp_base_url: str) -> respx.MockRouter:
    """Create a respx mock router scoped to the Bitpanda base URL."""
    with respx.mock(base_url=bp_base_url) as router:
        yield router


@pytest.fixture
async def bp_client(mock_router: respx.MockRouter, bp_base_url: str) -> BitpandaClient:
    """BitpandaClient wired to the mocked HTTP transport."""
    http = httpx.AsyncClient(base_url=bp_base_url)
    try:
        yield BitpandaClient(http, api_key="test-key")
    finally:
        await http.aclose()


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
    register(server)
    return server


@pytest.fixture
async def mcp_client(mcp_server: FastMCP) -> Client:
    """FastMCP test client."""
    async with Client(mcp_server) as client:
        yield client
