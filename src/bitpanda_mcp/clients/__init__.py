"""Client utilities for Bitpanda MCP tools."""

from fastmcp import Context
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from bitpanda_mcp.clients.bitpanda import BitpandaClient


def get_bp_client(ctx: Context) -> BitpandaClient:
    """Return a BitpandaClient for the current request.

    - **stdio mode**: uses the pre-built client from lifespan (``ctx.lifespan_context["bp"]``).
    - **HTTP mode**: creates a per-request client from the caller's Bearer token.
    """
    if "bp" in ctx.lifespan_context:
        return ctx.lifespan_context["bp"]

    token = get_access_token()
    if token is None:
        raise ToolError("Authentication required — send your Bitpanda API key as a Bearer token")

    return BitpandaClient(ctx.lifespan_context["http"], token.token)
