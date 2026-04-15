"""MCP server for Bitpanda — portfolio, wallets, trading, market data."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bitpanda-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
