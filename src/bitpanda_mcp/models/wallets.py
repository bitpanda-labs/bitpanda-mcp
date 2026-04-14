from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Wallet(BaseModel):
    """A single crypto wallet entry from the Bitpanda API."""

    model_config = ConfigDict(extra="ignore")

    wallet_id: str = Field(description="Wallet UUID")
    asset_id: str = Field(description="Asset UUID")
    wallet_type: str | None = Field(default=None, description="e.g. STAKING, CRYPTO_INDEX")
    index_asset_id: str | None = Field(default=None, description="Index asset UUID if applicable")
    last_credited_at: datetime = Field(description="Last credit timestamp")
    balance: float = Field(description="Current balance")


class FiatWallet(BaseModel):
    """A fiat currency wallet (EUR, USD, GBP, CHF)."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Fiat wallet UUID")
    type: str = Field(default="fiat", description="Wallet type")
    fiat_id: str = Field(description="Fiat currency UUID")
    fiat_symbol: str = Field(description="Currency code (EUR, USD, etc.)")
    balance: str = Field(description="Current balance")
    name: str = Field(default="", description="Wallet name")
