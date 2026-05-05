# Bitpanda MCP Server

[![CI](https://github.com/bitpanda-labs/bitpanda-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/bitpanda-labs/bitpanda-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

The official [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for [Bitpanda](https://www.bitpanda.com). Connects AI agents — Claude, Cursor, VS Code Copilot, and any MCP-compatible client — directly to the Bitpanda API, giving them secure, read-only access to your asset portfolio, wallet balances, trade history, and real-time market prices.

Built with [FastMCP 3.x](https://gofastmcp.com), Python 3.11+, and [uv](https://docs.astral.sh/uv/).

## Install the Bitpanda MCP Server

### Claude Code

```bash
claude mcp add bitpanda -e BITPANDA_API_KEY=your-key -- uvx --from git+https://github.com/bitpanda-labs/bitpanda-mcp bitpanda-mcp
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bitpanda": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/bitpanda-labs/bitpanda-mcp", "bitpanda-mcp"],
      "env": {
        "BITPANDA_API_KEY": "your-key"
      }
    }
  }
}
```

### Cursor / VS Code / Windsurf / any MCP client

```bash
uvx --from git+https://github.com/bitpanda-labs/bitpanda-mcp bitpanda-mcp
```

Set `BITPANDA_API_KEY` in your environment or `.env` file.

Get your Bitpanda API key at [web.bitpanda.com/apikey](https://web.bitpanda.com/apikey).

## What Can You Do With Bitpanda MCP?

- **Analyze your portfolio with Claude** — ask "what's my BTC allocation?" or "show me my top performing assets this month"
- **Get real-time asset prices** — BTC, ETH, and hundreds of other assets via natural language
- **Review trade and transaction history** — "summarize my trades from last quarter" or "show me recent transactions"
- **Build AI agents that interact with Bitpanda data** — integrate Bitpanda portfolio data into any MCP-compatible AI workflow
- **Automate reporting** — feed wallet balances and trade history into AI-powered analysis pipelines

## Available MCP Tools

| Tool | Category | Description |
|------|----------|-------------|
| `get_portfolio` | portfolio | Aggregated portfolio view across all assets with EUR valuations and `sort`/`sort_by` |
| `get_price` | market-data | Current ticker price and currency for any asset by symbol (BTC, ETH, SOL, and more) |
| `list_prices` | market-data | Ticker prices for held assets with ticker data, or a capped market-wide list with `all=true`/`all_assets=true` and `limit` |
| `get_asset` | market-data | Asset metadata by asset UUID |
| `list_wallets` | wallets | All Bitpanda asset wallet balances, with `non_zero`, `asset_id`, `page_size`, and `limit` filters |
| `list_transactions` | transactions | Raw asset transaction history with `wallet_id`, `flow`, `asset_id`, date filters, and `all=true` |
| `list_trades` | trades | Normalized buy/sell activity derived from asset transactions, with `operation`/`trade_type`, `asset_type`, date filters, and `all=true` |

All tools are **read-only** and annotated with `readOnlyHint=true`. The server never writes to or modifies your Bitpanda account.

## MCP Prompts

| Prompt | Description |
|--------|-------------|
| `portfolio_summary` | Analyze portfolio composition and identify concentration risk |
| `recent_activity` | Summarize recent trades and asset transactions |

## Self-Hosted Bitpanda MCP Server (HTTP / Docker)

Run the server as a remote HTTP service — multiple users each authenticate per-request with their own Bitpanda API key in the `X-Api-Key` header. Stateless design supports horizontal scaling.

### Start the HTTP server

```bash
FASTMCP_TRANSPORT=streamable-http \
FASTMCP_HOST=0.0.0.0 \
FASTMCP_PORT=8000 \
uv run bitpanda-mcp
```

Or with Docker (multi-stage build — runtime image contains no build tools or source code):

```bash
docker build -f ci/docker/Dockerfile -t bitpanda-mcp .
docker run -p 8000:8000 bitpanda-mcp
```

### Connect from any MCP client

```json
{
  "mcpServers": {
    "bitpanda": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-Api-Key": "YOUR_BITPANDA_API_KEY"
      }
    }
  }
}
```

Health check: `GET /healthz` → `{"status": "ok"}`.

## Configuration & Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BITPANDA_API_KEY` | stdio only | — | Bitpanda API key (in HTTP mode, each client sends their own key as `X-Api-Key`) |
| `BITPANDA_BASE_URL` | No | `https://developer.bitpanda.com` | Bitpanda API base URL |
| `REQUEST_TIMEOUT_S` | No | `30` | HTTP request timeout in seconds |
| `FASTMCP_TRANSPORT` | No | `stdio` | Transport: `stdio` or `streamable-http` |
| `FASTMCP_HOST` | No | `127.0.0.1` | HTTP bind address |
| `FASTMCP_PORT` | No | `8000` | HTTP port |
| `FASTMCP_STATELESS_HTTP` | No | `false` | Stateless mode for horizontal scaling |
| `MCP_AUTH_HEADER` | No | `X-Api-Key` | Header name for per-request API keys in HTTP mode. Override only if your gateway requires a different header. |

## Frequently Asked Questions

**Do I need a Bitpanda account?**  
Yes — you need an active [Bitpanda](https://www.bitpanda.com) account and a Bitpanda API key. Generate one at [web.bitpanda.com/apikey](https://web.bitpanda.com/apikey).

**Is this the official Bitpanda MCP server?**  
Yes. This repository is maintained by Bitpanda Labs and is the official MCP integration for the Bitpanda platform.

**What is the Model Context Protocol (MCP)?**  
MCP is an open standard that lets AI assistants connect to external data sources and tools in a structured, secure way. It's supported by Claude, Cursor, VS Code, Windsurf, and a growing ecosystem of AI development tools.

**Can Claude write to my Bitpanda account or place trades?**  
No. All tools exposed by this server are strictly read-only. The server cannot place orders, move funds, or modify your account in any way.

**Does this work with Claude.ai or ChatGPT?**  
It works with Claude Code (CLI) and Claude Desktop. ChatGPT and other OpenAI-based tools can connect via the remote HTTP mode if they support MCP or streamable-http. Any MCP-compatible client is supported.

## Development

Requires Python 3.11+.

```bash
git clone https://github.com/bitpanda-labs/bitpanda-mcp && cd bitpanda-mcp
uv sync
cp .env.example .env  # add your Bitpanda API key

uv run pytest                  # tests (100% coverage enforced)
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
uv build                       # build wheel + sdist
```

CI runs lint, tests on Python 3.11–3.14, and verifies the wheel installs cleanly.

## License

[Apache 2.0](LICENSE)
