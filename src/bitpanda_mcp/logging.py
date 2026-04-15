"""Structured logging with PII filtering for the Bitpanda MCP server.

Uses only stdlib ``logging``. JSON output for production (CloudWatch-compatible),
plain console output for local development. PII filter redacts API keys and tokens.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

_STRING_RE = re.compile(
    r"(X-Api-Key|Authorization)\s*[:=]\s*\S+(?:\s+\S+)*"
    r"|Bearer\s+\S+",
    re.IGNORECASE,
)
_KEY_RE = re.compile(r"api.?key|auth|bearer|token", re.IGNORECASE)
_REDACTED = "***"

# Standard LogRecord attributes — everything NOT in this set is a user-supplied extra field.
_BUILTIN_ATTRS = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def _redact_value(value: Any) -> Any:
    """Recursively redact sensitive patterns from strings, dicts, and lists."""
    if isinstance(value, str):
        return _STRING_RE.sub(_REDACTED, value)
    if isinstance(value, dict):
        return {k: _REDACTED if _KEY_RE.search(k) else _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    return value


class PiiFilter(logging.Filter):
    """Redact API keys and tokens from log records before formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact_value(record.msg)
        if isinstance(record.args, dict):
            record.args = _redact_value(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(_redact_value(a) for a in record.args)
        for key in record.__dict__:
            if key not in _BUILTIN_ATTRS:
                val = getattr(record, key)
                if isinstance(val, (str, dict, list)):
                    setattr(record, key, _redact_value(val))
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for CloudWatch / structured log systems."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": message,
        }
        for key, value in record.__dict__.items():
            if key not in _BUILTIN_ATTRS:
                entry[key] = value
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = _redact_value(self.formatException(record.exc_info))
        return json.dumps(entry, default=str)


def configure_logging(*, json_output: bool = True) -> None:
    """Configure logging for the server. Call once at startup.

    Args:
        json_output: True for JSON lines (production), False for console (dev).

    """
    logger = logging.getLogger("bitpanda_mcp")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.addFilter(PiiFilter())

    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    logger.addHandler(handler)
    logger.propagate = False
