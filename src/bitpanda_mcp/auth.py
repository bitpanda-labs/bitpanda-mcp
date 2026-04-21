"""Bearer token authentication for remote HTTP mode.

Users pass their Bitpanda API key as a Bearer token. The verifier accepts any
non-empty token and makes it available to tools via ``get_access_token()``.
"""

from fastmcp.server.auth import AccessToken, TokenVerifier


class BearerKeyVerifier(TokenVerifier):
    """Accept any non-empty bearer token as a Bitpanda API key.

    Token validity is decided by the Bitpanda API per request (401/403);
    this verifier only filters out empty tokens to avoid an extra round-trip.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token:
            return None
        return AccessToken(token=token, client_id="bearer", scopes=[])
