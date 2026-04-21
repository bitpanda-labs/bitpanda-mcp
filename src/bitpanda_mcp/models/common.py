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
    """Pagination metadata envelope returned by Bitpanda collection endpoints."""

    model_config = ConfigDict(extra="ignore")

    total_count: int = 0
    page_size: int | None = None
    next_cursor: str | None = None


class Page(BaseModel):
    """Generic cursor-paginated response wrapper.

    Real responses have shape
    ``{"data": [...], "meta": {"total_count", "page_size", "next_cursor"}, "links": {...}}``.
    """

    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]] = Field(default_factory=list)
    meta: PageMeta = Field(default_factory=PageMeta)
