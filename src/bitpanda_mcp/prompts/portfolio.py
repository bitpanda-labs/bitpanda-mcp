def portfolio_summary() -> str:
    """Analyze my Bitpanda portfolio and provide a summary."""
    return (
        "Please use the get_portfolio tool to fetch my current Bitpanda portfolio, then:\n"
        "1. Show each holding with its name, balance, EUR value, and percentage of total\n"
        "2. Highlight my largest positions\n"
        "3. Note any concentration risk (single asset > 30% of portfolio)\n"
        "4. Show total portfolio value in EUR"
    )


def recent_activity() -> str:
    """Show and analyze my recent Bitpanda activity."""
    return (
        "Please use list_trades for recent buy/sell activity, list_fiat_transactions "
        "for fiat deposits and withdrawals, and list_crypto_transactions for crypto "
        "deposits and transfers, then:\n"
        "1. Summarize recent trades with amounts and dates\n"
        "2. Show any fiat deposits or withdrawals\n"
        "3. Calculate net investment flow (deposits minus withdrawals) if visible"
    )
