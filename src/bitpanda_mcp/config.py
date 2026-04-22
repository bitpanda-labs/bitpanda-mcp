from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bitpanda_api_key: str | None = Field(
        default=None,
        description="Bitpanda API key. Required for stdio; in HTTP mode sent per-request as Bearer token.",
    )
    bitpanda_base_url: str = Field(default="https://api.bitpanda.com")

    request_timeout_s: float = Field(default=30.0, ge=1, le=120)

    server_transport: str = Field(
        default="stdio",
        alias="FASTMCP_TRANSPORT",
        description="Transport mode read from FastMCP env var.",
    )
