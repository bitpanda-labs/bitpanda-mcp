import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from bitpanda_mcp.models.common import BitpandaAPIError, Page

_ERROR_THRESHOLD = 400
_MAX_PAGES = 500

_log = logging.getLogger(__name__)


class BaseClient:
    """Shared async HTTP client logic for Bitpanda APIs."""

    def __init__(self, http: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
        self._http = http
        self._auth_headers = auth_headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an authenticated GET request and return parsed JSON.

        Raises ``BitpandaAPIError`` on 4xx/5xx responses, network errors,
        and non-JSON responses (e.g. HTML proxy pages).
        """
        try:
            resp = await self._http.get(path, headers=self._auth_headers, params=params)
        except httpx.HTTPError as exc:
            _log.error("api_network_error", extra={"path": path, "error": str(exc)})
            raise BitpandaAPIError(0, f"Network error: {exc}") from exc
        if resp.status_code >= _ERROR_THRESHOLD:
            detail = _extract_error_detail(resp)
            _log.warning("api_error", extra={"path": path, "status": resp.status_code, "detail": detail})
            raise BitpandaAPIError(resp.status_code, detail)
        try:
            return resp.json()
        except ValueError as exc:
            raise BitpandaAPIError(0, "Invalid JSON in API response") from exc

    async def _paginate_all(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        cursor_param: str = "after",
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a cursor-paginated endpoint."""
        all_items: list[dict[str, Any]] = []
        async for page in self._paginate_pages(
            path,
            params=params,
            cursor_param=cursor_param,
            page_size=page_size,
        ):
            all_items.extend(page.data)

            if limit and len(all_items) >= limit:
                return all_items[:limit]

        return all_items

    async def _paginate_pages(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        cursor_param: str = "after",
        page_size: int = 25,
    ) -> AsyncIterator[Page]:
        """Yield parsed pages from a cursor-paginated endpoint."""
        base_params = dict(params or {})
        base_params["page_size"] = page_size
        cursor: str | None = None

        for _ in range(_MAX_PAGES):
            request_params = {**base_params}
            if cursor:
                request_params[cursor_param] = cursor
            raw = await self._get(path, request_params)
            page = Page.model_validate(raw)
            yield page

            if not page.has_next_page:
                break

            cursor = page.get_next_cursor()
            if not cursor:
                break


def _extract_error_detail(resp: httpx.Response) -> str:
    """Best-effort extraction of error message from an API response."""
    try:
        body = resp.json()
        if "message" in body:
            return body["message"]
        errors = body.get("errors")
        if errors and isinstance(errors, list):
            first = errors[0]
            return first.get("title") or first.get("detail") or resp.text
        return resp.text
    except Exception:
        return resp.text
