# CLAUDE.md

## Project

bitpanda-mcp — MCP server for the Bitpanda platform. Built with FastMCP 3.x, Python 3.13+, uv.

## Commands

```bash
uv sync                        # install dependencies
uv run pytest                  # run tests
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
uv run bitpanda-mcp            # run the MCP server (stdio)
```

## Architecture

- `src/bitpanda_mcp/server.py` — FastMCP server, lifespan, tool registration
- `src/bitpanda_mcp/config.py` — pydantic-settings, env vars
- `src/bitpanda_mcp/clients/` — async httpx clients for Bitpanda API
- `src/bitpanda_mcp/tools/` — MCP tool functions
- `src/bitpanda_mcp/models/` — Pydantic models for API responses
- `src/bitpanda_mcp/resources/` — MCP resources
- `src/bitpanda_mcp/prompts/` — MCP prompt templates
- `tests/` — pytest + respx mocks

Tools access shared httpx clients via `ctx.lifespan_context["bp"]`. Errors use `ToolError` from `fastmcp.exceptions`. All tools are read-only.

## Commits

Use conventional commits. Subject line only, no body, no description.

Format: `type: short description`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `style`

Examples:
- `feat: add list_fiat_wallets tool`
- `fix: correct ticker field names to match API`
- `docs: update README install instructions`

Rules:
- **No commit body** — subject line only, always
- **No Co-Authored-By** — never add co-author attributions
- **No Anthropic attribution** — never add any Anthropic or Claude co-author lines
- Keep subject under 72 characters
- Use imperative mood ("add" not "added")
- Lowercase after the type prefix

## Code style

- ruff handles all linting and formatting
- Line length: 110
- Use `ToolError` for tool errors, never return error dicts
- Use `ToolAnnotations(readOnlyHint=True, openWorldHint=True)` for all Bitpanda tools
- Tag tools by category: `portfolio`, `market-data`, `assets`, `wallets`, `transactions`, `trades`
- Models use `ConfigDict(extra="ignore")` to tolerate extra API fields
- Tests use respx for HTTP mocking and FastMCP `Client` for end-to-end tool tests
