from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BitpandaAPIError(Exception):
    """Error returned by a Bitpanda API call."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

    @property
    def is_auth_error(self) -> bool:
        return self.status_code in (401, 403)


class PageMeta(BaseModel):
    """Legacy pagination metadata envelope returned by collection endpoints."""

    model_config = ConfigDict(extra="ignore")

    total_count: int = 0
    page_size: int | None = None
    next_cursor: str | None = None


class Page(BaseModel):
    """Generic cursor-paginated response wrapper."""

    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]] = Field(default_factory=list)
    start_cursor: str | None = None
    end_cursor: str | None = None
    next_cursor: str | None = None
    has_next_page: bool = False
    has_previous_page: bool = False
    page_size: int | None = None

    def get_next_cursor(self) -> str | None:
        return self.next_cursor or self.end_cursor
