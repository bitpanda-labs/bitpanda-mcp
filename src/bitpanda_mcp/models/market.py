from pydantic import BaseModel, ConfigDict, Field


class TickerEntry(BaseModel):
    """A single entry from the Bitpanda ticker API."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Asset UUID")
    symbol: str = Field(description="Ticker symbol")
    type: str = Field(description="Asset type (e.g. cryptocoin, metal)")
    price: str = Field(description="Current price in EUR")
    price_change_day: str = Field(default="0", description="24h price change percentage")
    name: str = Field(default="", description="Asset name (may not be present in ticker)")


class Ticker:
    """Indexed collection of ticker entries for fast lookup."""

    def __init__(self, entries: list[TickerEntry]) -> None:
        self.entries = entries
        self.by_id: dict[str, TickerEntry] = {e.id: e for e in entries}
        self.by_symbol: dict[str, TickerEntry] = {e.symbol.upper(): e for e in entries}

    def get_by_symbol(self, symbol: str) -> TickerEntry | None:
        return self.by_symbol.get(symbol.upper())

    def get_by_id(self, asset_id: str) -> TickerEntry | None:
        return self.by_id.get(asset_id)
