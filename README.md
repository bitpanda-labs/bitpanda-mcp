# bitpanda-mcp

MCP server for the Bitpanda platform — portfolio, wallets, trading, market data.

Built with [FastMCP 3.x](https://gofastmcp.com), Python 3.11+, and [uv](https://docs.astral.sh/uv/).

## Quick Install

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

## Tools (7)

| Tool | Tags | Description |
|------|------|-------------|
| `get_portfolio` | portfolio | Aggregated portfolio view with EUR valuations |
| `get_price` | market-data | Current EUR price for an asset by symbol (BTC, ETH, etc.) |
| `list_wallets` | wallets | Crypto wallet balances (with `non_zero` filter) |
| `list_fiat_wallets` | wallets | Fiat currency wallets (EUR, USD, GBP, CHF, ...) |
| `list_fiat_transactions` | transactions | Fiat wallet transactions (with optional `status` filter) |
| `list_crypto_transactions` | transactions | Crypto wallet transactions (deposits, withdrawals, transfers) |
| `list_trades` | trades | Buy/sell trade history (with optional `trade_type` filter) |

All tools are read-only and annotated with `readOnlyHint=true`.

## Prompts

| Prompt | Description |
|--------|-------------|
| `portfolio_summary` | Analyze portfolio with concentration risk |
| `recent_activity` | Summarize recent trades and fiat activity |

## Remote Hosting (HTTP Mode)

The server can also run as a remote HTTP service (e.g. at `mcp.bitpanda.com`). Users connect with a URL and pass their Bitpanda API key as a Bearer token.

### Run the HTTP server

```bash
FASTMCP_TRANSPORT=streamable-http FASTMCP_HOST=0.0.0.0 FASTMCP_PORT=8000 uv run bitpanda-mcp
```

Or with Docker (multi-stage build — runtime image has no build tools):

```bash
docker build -f ci/docker/Dockerfile -t bitpanda-mcp .
docker run -p 8000:8000 bitpanda-mcp
```

### Connect from any MCP client

```json
{
  "mcpServers": {
    "bitpanda": {
      "url": "https://mcp.bitpanda.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_BITPANDA_API_KEY"
      }
    }
  }
}
```

Health check: `GET /healthz` returns `{"status": "ok"}`.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BITPANDA_API_KEY` | stdio only | — | Bitpanda API key (in HTTP mode, sent per-request as Bearer token) |
| `BITPANDA_BASE_URL` | No | `https://api.bitpanda.com` | API base URL |
| `REQUEST_TIMEOUT_S` | No | `30` | HTTP timeout (seconds) |
| `FASTMCP_TRANSPORT` | No | `stdio` | Transport: `stdio` or `streamable-http` |
| `FASTMCP_HOST` | No | `127.0.0.1` | HTTP bind address |
| `FASTMCP_PORT` | No | `8000` | HTTP port |
| `FASTMCP_STATELESS_HTTP` | No | `false` | Stateless mode for horizontal scaling |

Get your API key at [web.bitpanda.com/apikey](https://web.bitpanda.com/apikey).

## Development

Requires Python 3.11+.

```bash
git clone https://github.com/bitpanda-labs/bitpanda-mcp && cd bitpanda-mcp
uv sync
cp .env.example .env  # edit with your API key

uv run pytest                  # tests (100% coverage)
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
uv build                       # build wheel + sdist
pip install dist/bitpanda_mcp-*.whl  # install and test the built wheel
```

CI runs lint, tests on Python 3.11–3.14, and verifies the wheel installs cleanly.
