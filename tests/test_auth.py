from collections.abc import MutableMapping
from typing import Any

from bitpanda_mcp.auth import ApiKeyHeaderMiddleware, BearerKeyVerifier

SAMPLE_KEY = "my-api-key-123"


async def test_verify_token_returns_access_token() -> None:
    verifier = BearerKeyVerifier()
    result = await verifier.verify_token(SAMPLE_KEY)
    assert result is not None
    assert result.token == SAMPLE_KEY
    assert result.client_id == "bearer"
    assert result.scopes == []


async def test_verify_empty_token_returns_none() -> None:
    verifier = BearerKeyVerifier()
    result = await verifier.verify_token("")
    assert result is None


# --- ApiKeyHeaderMiddleware ---


def _make_scope(headers: list[tuple[bytes, bytes]], scope_type: str = "http") -> MutableMapping[str, Any]:
    return {"type": scope_type, "headers": headers}


async def test_middleware_injects_authorization_from_custom_header() -> None:
    captured: dict[str, Any] = {}

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured["headers"] = dict(scope["headers"])

    mw = ApiKeyHeaderMiddleware(app, header_name="X-Api-Key")
    await mw(_make_scope([(b"x-api-key", b"secret-key")]), None, None)

    assert captured["headers"][b"authorization"] == b"Bearer secret-key"
    assert b"x-api-key" not in captured["headers"]


async def test_middleware_does_not_overwrite_existing_authorization() -> None:
    captured: dict[str, Any] = {}

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured["headers"] = dict(scope["headers"])

    mw = ApiKeyHeaderMiddleware(app, header_name="X-Api-Key")
    await mw(
        _make_scope(
            [
                (b"x-api-key", b"ignored"),
                (b"authorization", b"Bearer already-set"),
            ]
        ),
        None,
        None,
    )

    assert captured["headers"][b"authorization"] == b"Bearer already-set"


async def test_middleware_passthrough_when_custom_header_absent() -> None:
    captured: dict[str, Any] = {}

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured["headers"] = dict(scope["headers"])

    mw = ApiKeyHeaderMiddleware(app, header_name="X-Api-Key")
    await mw(_make_scope([]), None, None)

    assert b"authorization" not in captured["headers"]


async def test_middleware_ignores_non_http_scope() -> None:
    captured: dict[str, Any] = {}

    async def app(scope: Any, receive: Any, send: Any) -> None:
        captured["scope"] = scope

    mw = ApiKeyHeaderMiddleware(app, header_name="X-Api-Key")
    original_scope = _make_scope([(b"x-api-key", b"key")], scope_type="websocket")
    await mw(original_scope, None, None)

    assert captured["scope"] is original_scope
