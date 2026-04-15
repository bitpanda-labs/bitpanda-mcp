# CLAUDE.md

## Project

bitpanda-mcp — MCP server for the Bitpanda platform. Built with FastMCP 3.x, Python 3.11+, uv.

## Commands

```bash
uv sync                        # install dependencies
uv run pytest                  # run tests
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
uv run bitpanda-mcp            # run the MCP server (stdio)
uv build                       # build wheel + sdist into dist/
```

## Architecture

- `src/bitpanda_mcp/server.py` — FastMCP server, lifespan, tool registration
- `src/bitpanda_mcp/config.py` — pydantic-settings, env vars
- `src/bitpanda_mcp/auth.py` — Bearer token auth for HTTP mode
- `src/bitpanda_mcp/clients/` — async httpx clients, `get_bp_client()` for dual stdio/HTTP mode
- `src/bitpanda_mcp/tools/` — MCP tool functions (all read-only)
- `src/bitpanda_mcp/models/` — Pydantic models for API responses
- `src/bitpanda_mcp/resources/` — MCP resources
- `src/bitpanda_mcp/prompts/` — MCP prompt templates
- `ci/docker/` — multi-stage Dockerfile, entrypoint script
- `.github/workflows/` — CI (lint, test on 3.11–3.14, build) and publish (PyPI on release)
- `tests/` — pytest + respx mocks, 100% coverage

## Packaging

- src-layout with hatchling build backend
- Version single-sourced in `pyproject.toml`, read at runtime via `importlib.metadata`
- Console script entry point: `bitpanda-mcp` → `bitpanda_mcp.server:main`
- Installable via `pip install .`, `pip install git+https://...`, or from built wheel
- Docker: multi-stage build, runtime image has no uv/curl/source — only Python + installed venv

## Dual transport

- **stdio** (default): `BITPANDA_API_KEY` in env, single pre-built client
- **HTTP** (`FASTMCP_TRANSPORT=streamable-http`): per-request Bearer token auth, stateless for horizontal scaling
- Tools use `get_bp_client(ctx)` from `clients/__init__.py` which handles both modes

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

## Error handling

- `_get()` in `clients/base.py` catches `httpx.HTTPError` (network) and `ValueError` (non-JSON responses)
- All tool functions catch both `BitpandaAPIError` and `pydantic.ValidationError`
- Tools convert errors to `ToolError`; resources convert to `ResourceError`
- Never expose raw tracebacks to MCP clients

## Code style

- ruff handles all linting and formatting (target: Python 3.11)
- Line length: 110
- Use `ToolError` for tool errors, never return error dicts
- Use `ToolAnnotations(readOnlyHint=True, openWorldHint=True)` for all Bitpanda tools
- Tag tools by category: `portfolio`, `market-data`, `assets`, `wallets`, `transactions`, `trades`
- Models use `ConfigDict(extra="ignore")` to tolerate extra API fields

## Testing

- pytest + respx for HTTP mocking, FastMCP `Client` for end-to-end tool tests
- 100% coverage enforced — direct unit tests for paths unreachable through MCP protocol
- CI matrix: Python 3.11, 3.12, 3.13, 3.14
