from typing import Any

import httpx

from bitpanda_mcp.models.common import BitpandaAPIError, CursorPage

_ERROR_THRESHOLD = 400
_MAX_PAGES = 500


class BaseClient:
    """Shared async HTTP client logic for Bitpanda APIs."""

    def __init__(self, http: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
        self._http = http
        self._auth_headers = auth_headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform an authenticated GET request and return parsed JSON.

        Raises ``BitpandaAPIError`` on non-2xx/3xx responses.
        """
        resp = await self._http.get(path, headers=self._auth_headers, params=params)
        if resp.status_code >= _ERROR_THRESHOLD:
            detail = _extract_error_detail(resp)
            raise BitpandaAPIError(resp.status_code, detail)
        return resp.json()

    async def _paginate_all(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = 25,
        cursor_param: str = "after",
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a cursor-paginated endpoint.

        Args:
            path: API path.
            params: Extra query parameters (filters).
            page_size: Items per page.
            cursor_param: Name of the cursor query parameter ("after" or "cursor").
            limit: Max total items to return. 0 means unlimited.

        Returns:
            Flat list of all ``data`` items across pages.

        """
        all_items: list[dict[str, Any]] = []
        request_params = dict(params or {})
        request_params["page_size"] = page_size
        cursor: str | None = None

        for _ in range(_MAX_PAGES):
            if cursor:
                request_params[cursor_param] = cursor

            raw = await self._get(path, request_params)
            page = CursorPage.model_validate(raw)
            all_items.extend(page.data)

            if limit and len(all_items) >= limit:
                return all_items[:limit]

            if not page.has_next_page or not page.cursor:
                break

            cursor = page.cursor

        return all_items


def _extract_error_detail(resp: httpx.Response) -> str:
    """Best-effort extraction of error message from an API response."""
    try:
        body = resp.json()
        if "message" in body:
            return body["message"]
        errors = body.get("errors")
        if errors and isinstance(errors, list):
            return errors[0].get("title", resp.text)
        return resp.text
    except Exception:
        return resp.text
