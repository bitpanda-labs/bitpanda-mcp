import pytest

from bitpanda_mcp.config import Settings


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BITPANDA_API_KEY", "my-key")
    s = Settings()
    assert s.bitpanda_api_key == "my-key"
    assert s.bitpanda_base_url == "https://developer.bitpanda.com"
    assert s.request_timeout_s == 30.0
    assert s.server_transport == "stdio"


def test_settings_api_key_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BITPANDA_API_KEY", raising=False)
    s = Settings(_env_file=None)
    assert s.bitpanda_api_key is None


def test_settings_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BITPANDA_API_KEY", "key")
    monkeypatch.setenv("BITPANDA_BASE_URL", "https://custom.example.com")
    s = Settings()
    assert s.bitpanda_base_url == "https://custom.example.com"


def test_settings_transport_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BITPANDA_API_KEY", raising=False)
    monkeypatch.setenv("FASTMCP_TRANSPORT", "streamable-http")
    s = Settings(_env_file=None)
    assert s.server_transport == "streamable-http"
    assert s.bitpanda_api_key is None
