from bitpanda_mcp.auth import BearerKeyVerifier

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
