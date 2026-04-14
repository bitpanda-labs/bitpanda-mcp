from typing import Any

from pydantic import BaseModel, ConfigDict


class BitpandaAPIError(Exception):
    """Error returned by a Bitpanda API call."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

    @property
    def is_auth_error(self) -> bool:
        return self.status_code in (401, 403)


class CursorPage(BaseModel):
    """Generic cursor-paginated response wrapper."""

    model_config = ConfigDict(extra="ignore")

    data: list[dict[str, Any]]
    has_next_page: bool = False
    has_previous_page: bool = False
    end_cursor: str | None = None
    next_cursor: str | None = None
    page_size: int | str | None = None

    @property
    def cursor(self) -> str | None:
        """Return the cursor for the next page, handling both field names."""
        return self.next_cursor or self.end_cursor
