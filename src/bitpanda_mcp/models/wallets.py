from pydantic import BaseModel, ConfigDict, Field


class Wallet(BaseModel):
    """A crypto wallet after flattening the JSON:API ``{id, type, attributes}`` envelope."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Wallet UUID")
    cryptocoin_id: str = Field(default="", description="Numeric asset ID")
    cryptocoin_symbol: str = Field(default="", description="Asset symbol (BTC, ETH, ...)")
    balance: str = Field(default="0", description="Current balance (string-decimal)")
    name: str = Field(default="", description="Wallet name")
    is_default: bool = Field(default=False)
    is_index: bool = Field(default=False)
    deleted: bool = Field(default=False)
    pending_transactions_count: int = Field(default=0)

    @property
    def balance_float(self) -> float:
        try:
            return float(self.balance)
        except (ValueError, TypeError):
            return 0.0


class FiatWallet(BaseModel):
    """A fiat wallet after flattening the JSON:API envelope."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Fiat wallet UUID")
    fiat_id: str = Field(default="", description="Numeric fiat ID")
    fiat_symbol: str = Field(default="", description="Currency code (EUR, USD, ...)")
    balance: str = Field(default="0", description="Current balance")
    name: str = Field(default="", description="Wallet name")
    pending_transactions_count: int = Field(default=0)
