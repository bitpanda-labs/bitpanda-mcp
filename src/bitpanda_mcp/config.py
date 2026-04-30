from typing import Annotated

from pydantic import Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

HeaderName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bitpanda_api_key: str | None = Field(
        default=None,
        description="Bitpanda API key. Required for stdio; in HTTP mode sent per-request via X-Api-Key.",
    )
    bitpanda_base_url: str = Field(default="https://developer.bitpanda.com")

    request_timeout_s: float = Field(default=30.0, ge=1, le=120)

    server_transport: str = Field(
        default="stdio",
        alias="FASTMCP_TRANSPORT",
        description="Transport mode read from FastMCP env var.",
    )
    server_host: str = Field(default="127.0.0.1", alias="FASTMCP_HOST")
    server_port: int = Field(default=8000, alias="FASTMCP_PORT", ge=1, le=65535)

    mcp_auth_header: HeaderName = Field(default="X-Api-Key", alias="MCP_AUTH_HEADER")
