from pydantic import BaseModel, ConfigDict, Field


class Wallet(BaseModel):
    """An asset wallet balance."""

    model_config = ConfigDict(extra="ignore")

    wallet_id: str = Field(description="Wallet UUID")
    asset_id: str = Field(default="", description="Asset UUID")
    wallet_type: str = Field(default="", description="Wallet type")
    index_asset_id: str = Field(default="", description="Index asset UUID")
    last_credited_at: str = Field(default="", description="Last credited timestamp")
    balance: str = Field(default="0", description="Current balance (string-decimal)")

    @property
    def balance_float(self) -> float:
        try:
            return float(self.balance)
        except (ValueError, TypeError):
            return 0.0

    @property
    def effective_wallet_type(self) -> str:
        return self.wallet_type or "regular"
