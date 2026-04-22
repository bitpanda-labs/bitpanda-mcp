"""Tests for prompt templates."""

from bitpanda_mcp.prompts.portfolio import portfolio_summary, recent_activity


def test_portfolio_summary_returns_instructions() -> None:
    result = portfolio_summary()
    assert "get_portfolio" in result
    assert "EUR" in result


def test_recent_activity_returns_instructions() -> None:
    result = recent_activity()
    assert "list_trades" in result
    assert "list_fiat_transactions" in result
