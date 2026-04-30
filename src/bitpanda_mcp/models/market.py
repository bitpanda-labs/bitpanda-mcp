from pydantic import BaseModel, ConfigDict, Field


class TickerEntry(BaseModel):
    """A single ticker entry."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Asset UUID")
    name: str = Field(default="", description="Asset name")
    symbol: str = Field(description="Ticker symbol, e.g. BTC")
    type: str = Field(default="", description="Asset type")
    currency: str = Field(default="EUR", description="Price currency")
    price: str = Field(description="Current price")
    price_change_day: str = Field(default="", description="24h price change percentage")

    @property
    def price_eur(self) -> str:
        return self.price if self.currency.upper() == "EUR" else "0"


class Ticker:
    """Indexed collection of ticker entries."""

    def __init__(self, entries: list[TickerEntry]) -> None:
        self.entries = entries
        self.by_symbol: dict[str, TickerEntry] = {e.symbol.upper(): e for e in entries}
        self.by_id: dict[str, TickerEntry] = {e.id: e for e in entries}

    def get_by_symbol(self, symbol: str) -> TickerEntry | None:
        return self.by_symbol.get(symbol.upper())

    def get_by_asset_id(self, asset_id: str) -> TickerEntry | None:
        return self.by_id.get(asset_id)
