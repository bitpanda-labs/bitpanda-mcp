from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    """An asset transaction."""

    model_config = ConfigDict(extra="ignore")

    transaction_id: str = Field(description="Transaction UUID")
    operation_id: str = Field(default="", description="Operation UUID")
    asset_id: str = Field(default="", description="Asset UUID")
    account_id: str = Field(default="", description="Account UUID")
    wallet_id: str = Field(default="", description="Wallet UUID")
    asset_amount: str = Field(default="0", description="Asset amount")
    fee_amount: str = Field(default="0", description="Fee amount")
    operation_type: str = Field(default="", description="Operation type")
    transaction_type: str = Field(default="", description="Transaction type")
    flow: str = Field(default="", description="incoming or outgoing")
    credited_at: str = Field(default="", description="Credited timestamp")
    compensates: str = Field(default="", description="Compensated transaction UUID")
    trade_id: str = Field(default="", description="Trade UUID")

    @property
    def is_trade(self) -> bool:
        return self.trade_id != "" and self.flow == "incoming" and self.operation_type in {"buy", "sell"}


class Trade(BaseModel):
    """A buy or sell operation derived from an asset transaction."""

    model_config = ConfigDict(extra="ignore")

    transaction_id: str = Field(description="Transaction UUID")
    trade_id: str = Field(description="Trade UUID")
    type: str = Field(description="buy or sell")
    asset_id: str = Field(default="", description="Asset UUID")
    asset_symbol: str = Field(default="", description="Asset symbol")
    asset_name: str = Field(default="", description="Asset name")
    asset_type: str = Field(default="", description="Asset type")
    asset_amount: str = Field(default="0", description="Asset amount")
    fee_amount: str = Field(default="0", description="Fee amount")
    credited_at: str = Field(default="", description="Credited timestamp")
    price_eur: str | None = Field(default=None, description="Current EUR price")
