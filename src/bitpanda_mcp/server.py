from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from bitpanda_mcp import __version__
from bitpanda_mcp.auth import BearerKeyVerifier
from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.config import Settings
from bitpanda_mcp.prompts import portfolio as portfolio_prompts
from bitpanda_mcp.resources import assets as asset_resources
from bitpanda_mcp.tools import assets as asset_tools
from bitpanda_mcp.tools import market as market_tools
from bitpanda_mcp.tools import portfolio as portfolio_tools
from bitpanda_mcp.tools import trading as trading_tools
from bitpanda_mcp.tools import transactions as transaction_tools
from bitpanda_mcp.tools import wallets as wallet_tools

READONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create shared API clients for the server lifetime.

    - **stdio mode** (``BITPANDA_API_KEY`` set): yields a pre-built ``BitpandaClient`` under ``"bp"``.
    - **HTTP mode** (no env key): yields only the shared ``httpx.AsyncClient`` under ``"http"``;
      per-request clients are built from the caller's Bearer token in ``get_bp_client()``.
    """
    settings = Settings()

    async with httpx.AsyncClient(
        base_url=settings.bitpanda_base_url,
        timeout=settings.request_timeout_s,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    ) as bp_http:
        ctx: dict[str, Any] = {"http": bp_http}

        if settings.bitpanda_api_key:
            ctx["bp"] = BitpandaClient(bp_http, settings.bitpanda_api_key)

        yield ctx


mcp = FastMCP(
    name="bitpanda-mcp",
    version=__version__,
    instructions=(
        "MCP server for Bitpanda. Use get_portfolio for a full overview of holdings with EUR values. "
        "Use get_price to check a specific asset price by symbol (e.g. BTC, ETH). "
        "Use list_trades to see recent buy/sell activity. "
        "Use list_wallets and list_fiat_wallets to see crypto and fiat balances separately. "
        "Use list_transactions, list_fiat_transactions, or list_crypto_transactions for detailed history. "
        "All data comes from the Bitpanda API and requires a valid API key."
    ),
    lifespan=lifespan,
    auth=BearerKeyVerifier(),
)

# --- Tools: Portfolio ---
mcp.tool(annotations=READONLY, tags={"portfolio"})(portfolio_tools.get_portfolio)

# --- Tools: Market data ---
mcp.tool(annotations=READONLY, tags={"market-data"})(market_tools.get_price)

# --- Tools: Assets ---
mcp.tool(annotations=READONLY, tags={"assets"})(asset_tools.get_asset)
mcp.tool(annotations=READONLY, tags={"assets"})(asset_tools.list_assets)

# --- Tools: Wallets ---
mcp.tool(annotations=READONLY, tags={"wallets"})(wallet_tools.list_wallets)
mcp.tool(annotations=READONLY, tags={"wallets"})(wallet_tools.list_fiat_wallets)

# --- Tools: Transactions ---
mcp.tool(annotations=READONLY, tags={"transactions"})(transaction_tools.list_transactions)
mcp.tool(annotations=READONLY, tags={"transactions"})(transaction_tools.list_fiat_transactions)
mcp.tool(annotations=READONLY, tags={"transactions"})(transaction_tools.list_crypto_transactions)

# --- Tools: Trades ---
mcp.tool(annotations=READONLY, tags={"trades"})(trading_tools.list_trades)

# --- Resources ---
mcp.resource("bitpanda://assets/catalog")(asset_resources.get_asset_catalog)

# --- Prompts ---
mcp.prompt()(portfolio_prompts.portfolio_summary)
mcp.prompt()(portfolio_prompts.recent_activity)


# --- Health check (HTTP mode only) ---
@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Health check endpoint for load balancers."""
    return JSONResponse({"status": "ok"})


def main() -> None:
    """Entry point for `bitpanda-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    main()
