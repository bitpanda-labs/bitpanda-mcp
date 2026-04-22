from pydantic import BaseModel, ConfigDict, Field


class TickerEntry(BaseModel):
    """A single entry derived from the Bitpanda ticker API.

    The ticker endpoint returns a flat ``{symbol: {currency: price}}`` dict; this model
    is the normalized per-symbol record the MCP uses internally.
    """

    model_config = ConfigDict(extra="ignore")

    symbol: str = Field(description="Ticker symbol, e.g. BTC")
    price_eur: str = Field(description="Current price in EUR, as returned by the API")


class Ticker:
    """Indexed collection of ticker entries keyed by symbol."""

    def __init__(self, entries: list[TickerEntry]) -> None:
        self.entries = entries
        self.by_symbol: dict[str, TickerEntry] = {e.symbol.upper(): e for e in entries}

    def get_by_symbol(self, symbol: str) -> TickerEntry | None:
        return self.by_symbol.get(symbol.upper())
