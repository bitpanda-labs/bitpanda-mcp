import logging
from typing import Any

import httpx

from bitpanda_mcp.models.common import BitpandaAPIError, Page

_ERROR_THRESHOLD = 400
_MAX_PAGES = 500

_log = logging.getLogger(__name__)


def flatten_jsonapi(record: Any) -> Any:
    """Flatten a JSON:API ``{id, type, attributes: {...}}`` record to a single-level dict.

    Non-dict inputs and records without ``attributes`` are returned unchanged.
    ``id`` and ``type`` are preserved at the top level, attributes take precedence
    for any other keys.
    """
    if not isinstance(record, dict):
        return record
    attrs = record.get("attributes")
    if not isinstance(attrs, dict):
        return record
    out: dict[str, Any] = {**attrs}
    if "id" in record:
        out["id"] = record["id"]
    if "type" in record and "type" not in attrs:
        out["type"] = record["type"]
    return out


class BaseClient:
    """Shared async HTTP client logic for Bitpanda APIs."""

    def __init__(self, http: httpx.AsyncClient, auth_headers: dict[str, str]) -> None:
        self._http = http
        self._auth_headers = auth_headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an authenticated GET request and return parsed JSON.

        Raises ``BitpandaAPIError`` on non-2xx/3xx responses, network errors,
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
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of a cursor-paginated endpoint and flatten JSON:API records.

        Bitpanda collection responses have shape::

            {"data": [{"id": "...", "type": "...", "attributes": {...}}],
             "meta": {"total_count": N, "page_size": K, "next_cursor": "uuid"},
             "links": {...}}

        Pagination advances via the ``cursor`` query parameter. Iteration stops when
        the API returns no ``next_cursor``, an empty page, or fewer items than
        ``page_size``.

        Args:
            path: API path.
            params: Extra query parameters (filters).
            page_size: Items per page.
            limit: Max total items to return. 0 means unlimited.

        Returns:
            Flat list of flattened records across all pages.

        """
        all_items: list[dict[str, Any]] = []
        base_params = dict(params or {})
        base_params["page_size"] = page_size
        cursor: str | None = None

        for _ in range(_MAX_PAGES):
            request_params = {**base_params}
            if cursor:
                request_params["cursor"] = cursor
            raw = await self._get(path, request_params)
            page = Page.model_validate(raw)
            all_items.extend(flatten_jsonapi(item) for item in page.data)

            if limit and len(all_items) >= limit:
                return all_items[:limit]

            cursor = page.meta.next_cursor
            if not cursor or not page.data or len(page.data) < page_size:
                break

        return all_items


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
