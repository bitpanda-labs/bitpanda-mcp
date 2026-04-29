import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import uvicorn
from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from bitpanda_mcp import __version__
from bitpanda_mcp.auth import ApiKeyHeaderMiddleware, BearerKeyVerifier
from bitpanda_mcp.clients.bitpanda import BitpandaClient
from bitpanda_mcp.config import Settings
from bitpanda_mcp.logging import configure_logging
from bitpanda_mcp.prompts import portfolio as portfolio_prompts
from bitpanda_mcp.tools import market as market_tools
from bitpanda_mcp.tools import portfolio as portfolio_tools
from bitpanda_mcp.tools import trading as trading_tools
from bitpanda_mcp.tools import transactions as transaction_tools
from bitpanda_mcp.tools import wallets as wallet_tools

READONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

_TOOLS: list[tuple[Callable[..., Any], set[str]]] = [
    (portfolio_tools.get_portfolio, {"portfolio"}),
    (market_tools.get_price, {"market-data"}),
    (wallet_tools.list_wallets, {"wallets"}),
    (wallet_tools.list_fiat_wallets, {"wallets"}),
    (transaction_tools.list_fiat_transactions, {"transactions"}),
    (transaction_tools.list_crypto_transactions, {"transactions"}),
    (trading_tools.list_trades, {"trades"}),
]

_PROMPTS: list[Callable[..., Any]] = [
    portfolio_prompts.portfolio_summary,
    portfolio_prompts.recent_activity,
]


def register(server: FastMCP) -> None:
    """Register every Bitpanda tool and prompt on ``server``."""
    for fn, tags in _TOOLS:
        server.tool(annotations=READONLY, tags=tags)(fn)
    for prompt in _PROMPTS:
        server.prompt()(prompt)


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Create shared API clients for the server lifetime.

    - **stdio mode**: yields a pre-built ``BitpandaClient`` under ``"bp"`` when
      ``BITPANDA_API_KEY`` is set in the environment.
    - **HTTP mode**: yields only the shared ``httpx.AsyncClient`` under ``"http"``;
      per-request clients are built from the caller's Bearer token in
      ``get_bp_client()``. ``BITPANDA_API_KEY`` is ignored in HTTP mode so a
      multi-tenant deployment cannot accidentally route every request through a
      single operator key.
    """
    settings = Settings()
    log = logging.getLogger(__name__)
    log.info("server_start", extra={"transport": settings.server_transport, "version": __version__})

    async with httpx.AsyncClient(
        base_url=settings.bitpanda_base_url,
        timeout=settings.request_timeout_s,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    ) as bp_http:
        ctx: dict[str, Any] = {"http": bp_http}

        if settings.server_transport == "stdio" and settings.bitpanda_api_key:
            ctx["bp"] = BitpandaClient(bp_http, settings.bitpanda_api_key)

        yield ctx

    log.info("server_stop")


mcp = FastMCP(
    name="bitpanda-mcp",
    version=__version__,
    instructions=(
        "MCP server for Bitpanda. Use get_portfolio for a full overview of holdings with EUR values. "
        "Use get_price to check a specific asset price by symbol (e.g. BTC, ETH). "
        "Use list_trades to see recent buy/sell activity. "
        "Use list_wallets and list_fiat_wallets to see crypto and fiat balances separately. "
        "Use list_fiat_transactions or list_crypto_transactions for detailed history. "
        "All data comes from the Bitpanda API and requires a valid API key."
    ),
    lifespan=lifespan,
    auth=BearerKeyVerifier(),
)

register(mcp)


# --- Health check (HTTP mode only) ---
@mcp.custom_route("/healthz", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    """Health check endpoint for load balancers."""
    return JSONResponse({"status": "ok"})


def build_http_app(settings: Settings) -> ASGIApp:
    app: ASGIApp = mcp.http_app()
    if settings.mcp_auth_header:
        app = ApiKeyHeaderMiddleware(app, header_name=settings.mcp_auth_header)
    return app


def main() -> None:
    """Entry point for `bitpanda-mcp` console script."""
    settings = Settings()
    configure_logging(json_output=settings.server_transport != "stdio")
    if settings.server_transport == "stdio":
        mcp.run()
        return

    uvicorn.run(
        build_http_app(settings),
        host=settings.server_host,
        port=settings.server_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
