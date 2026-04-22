"""Tests for structured logging and PII filtering."""

import json
import logging
import sys

from bitpanda_mcp.logging import JsonFormatter, PiiFilter, _redact_value, configure_logging

# --- _redact_value unit tests ---


def test_redact_api_key_in_string() -> None:
    result = _redact_value("X-Api-Key: secret-key-123")
    assert "secret-key-123" not in result
    assert "***" in result


def test_redact_bearer_token_in_string() -> None:
    result = _redact_value("Authorization: Bearer my-token-abc")
    assert "my-token-abc" not in result
    assert "***" in result


def test_redact_standalone_bearer() -> None:
    result = _redact_value("Bearer token123")
    assert "token123" not in result


def test_redact_preserves_trailing_context() -> None:
    """The regex must not swallow unrelated trailing tokens after the credential."""
    result = _redact_value("Authorization: Bearer abc request_id=42 user_id=17")
    assert "abc" not in result
    assert "request_id=42" in result
    assert "user_id=17" in result


def test_redact_api_key_preserves_trailing_context() -> None:
    result = _redact_value("X-Api-Key: secret-123 path=/v1/wallets status=200")
    assert "secret-123" not in result
    assert "path=/v1/wallets" in result
    assert "status=200" in result


def test_redact_case_insensitive() -> None:
    result = _redact_value("x-api-key: lowercase-key")
    assert "lowercase-key" not in result


def test_redact_dict_sensitive_key() -> None:
    result = _redact_value({"X-Api-Key": "secret", "safe": "value"})
    assert result["X-Api-Key"] == "***"
    assert result["safe"] == "value"


def test_redact_dict_authorization() -> None:
    result = _redact_value({"Authorization": "Bearer abc", "Content-Type": "application/json"})
    assert result["Authorization"] == "***"
    assert result["Content-Type"] == "application/json"


def test_redact_in_list() -> None:
    result = _redact_value(["Bearer token123", "clean"])
    assert "token123" not in result[0]
    assert result[1] == "clean"


def test_redact_nested_dict_in_list() -> None:
    result = _redact_value([{"api_key": "secret"}])
    assert result[0]["api_key"] == "***"


def test_redact_preserves_non_sensitive() -> None:
    assert _redact_value("hello world") == "hello world"
    assert _redact_value(42) == 42
    assert _redact_value(None) is None
    assert _redact_value(True) is True


# --- PiiFilter tests ---


def _make_record(msg: str = "test", **extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg=msg, args=(), exc_info=None
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_pii_filter_redacts_msg() -> None:
    record = _make_record("X-Api-Key: secret-123")
    PiiFilter().filter(record)
    assert "secret-123" not in record.msg


def test_pii_filter_redacts_extra_fields() -> None:
    record = _make_record("clean message", header="Bearer my-token")
    PiiFilter().filter(record)
    assert "my-token" not in record.header


def test_pii_filter_redacts_dict_args() -> None:
    record = _make_record("%(header)s")
    record.args = {"header": "X-Api-Key: secret"}
    PiiFilter().filter(record)
    assert "secret" not in record.args["header"]


def test_pii_filter_redacts_tuple_args() -> None:
    record = _make_record("header: %s")
    record.args = ("Bearer my-token",)
    PiiFilter().filter(record)
    assert "my-token" not in record.args[0]


def test_pii_filter_non_string_msg() -> None:
    record = _make_record("test")
    record.msg = 42  # non-string msg (e.g. lazy formatting)
    PiiFilter().filter(record)
    assert record.msg == 42


def test_pii_filter_no_args() -> None:
    record = _make_record("test")
    record.args = None
    PiiFilter().filter(record)
    assert record.args is None


# --- JsonFormatter tests ---


def test_json_formatter_output() -> None:
    record = _make_record("test_event")
    record.custom_field = "value"
    output = JsonFormatter().format(record)
    parsed = json.loads(output)
    assert parsed["event"] == "test_event"
    assert parsed["custom_field"] == "value"
    assert parsed["level"] == "info"
    assert "timestamp" in parsed
    assert parsed["logger"] == "test"


def test_json_formatter_with_exception() -> None:
    try:
        msg = "fail"
        raise ValueError(msg)
    except ValueError:
        record = _make_record("error_event")
        record.exc_info = sys.exc_info()
        output = JsonFormatter().format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


def test_json_formatter_redacts_exception_pii() -> None:
    try:
        msg = "X-Api-Key: secret-in-traceback"
        raise RuntimeError(msg)
    except RuntimeError:
        record = _make_record("error_with_pii")
        record.exc_info = sys.exc_info()
        output = JsonFormatter().format(record)
        assert "secret-in-traceback" not in output
        parsed = json.loads(output)
        assert "***" in parsed["exception"]


# --- configure_logging integration tests ---


def test_configure_logging_json(capfd) -> None:
    configure_logging(json_output=True)
    logger = logging.getLogger("bitpanda_mcp.test_json")
    logger.info("test_event", extra={"key": "value"})
    output = capfd.readouterr().err.strip()
    parsed = json.loads(output)
    assert parsed["event"] == "test_event"
    assert parsed["key"] == "value"
    assert "timestamp" in parsed


def test_configure_logging_console(capfd) -> None:
    configure_logging(json_output=False)
    logger = logging.getLogger("bitpanda_mcp.test_console")
    logger.info("console_event")
    output = capfd.readouterr().err
    assert "console_event" in output


def test_logging_redacts_in_json_mode(capfd) -> None:
    configure_logging(json_output=True)
    logger = logging.getLogger("bitpanda_mcp.test_redact")
    logger.info("api_call", extra={"header": "X-Api-Key: secret-key-abc"})
    output = capfd.readouterr().err.strip()
    assert "secret-key-abc" not in output
    parsed = json.loads(output)
    assert "***" in parsed["header"]
