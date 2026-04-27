"""Bearer token authentication for remote HTTP mode.

Users pass their Bitpanda API key as a Bearer token. The verifier accepts any
non-empty token and makes it available to tools via ``get_access_token()``.
"""

from fastmcp.server.auth import AccessToken, TokenVerifier
from starlette.types import ASGIApp, Receive, Scope, Send


class BearerKeyVerifier(TokenVerifier):
    """Accept any non-empty bearer token as a Bitpanda API key.

    Token validity is decided by the Bitpanda API per request (401/403);
    this verifier only filters out empty tokens to avoid an extra round-trip.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token:
            return None
        return AccessToken(token=token, client_id="bearer", scopes=[])


class ApiKeyHeaderMiddleware:
    def __init__(self, app: ASGIApp, header_name: str) -> None:
        self.app = app
        self.header = header_name.lower().encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = scope["headers"]
            key_value = next((v for k, v in headers if k == self.header), None)
            if key_value is not None and not any(k == b"authorization" for k, _ in headers):
                stripped = [(k, v) for k, v in headers if k != self.header]
                scope = {**scope, "headers": [*stripped, (b"authorization", b"Bearer " + key_value)]}
        await self.app(scope, receive, send)
