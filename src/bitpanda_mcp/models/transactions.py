from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionFlow = Literal["INCOMING", "OUTGOING"]


class Transaction(BaseModel):
    """A single transaction from the Bitpanda API."""

    model_config = ConfigDict(extra="ignore")

    transaction_id: str = Field(description="Transaction UUID")
    operation_id: str = Field(description="Operation UUID")
    asset_id: str = Field(description="Asset UUID")
    account_id: str = Field(description="Account UUID")
    wallet_id: str = Field(description="Wallet UUID")
    asset_amount: float = Field(description="Amount of the asset transacted")
    fee_amount: float = Field(description="Fee amount")
    operation_type: str = Field(description="Type of operation")
    transaction_type: str | None = Field(default=None, description="Transaction sub-type")
    flow: str = Field(description="INCOMING or OUTGOING")
    credited_at: datetime = Field(description="When the transaction was credited")
    trade_id: str | None = Field(default=None, description="Associated trade UUID, if any")
    order_id: int | None = Field(default=None, description="Associated order ID")


class Trade(BaseModel):
    """A trade from the Bitpanda /trades endpoint (buy or sell)."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Trade UUID")
    type: str = Field(description="buy or sell")
    status: str = Field(default="", description="Trade status")
    cryptocoin_id: str = Field(default="", description="Asset ID")
    cryptocoin_symbol: str = Field(default="", description="Asset symbol (BTC, ETH, etc.)")
    fiat_id: str = Field(default="", description="Fiat currency ID")
    amount_fiat: str = Field(default="0", description="Fiat amount")
    amount_cryptocoin: str = Field(default="0", description="Crypto amount")
    price: str = Field(default="0", description="Price per unit")
    fee: str = Field(default="0", description="Fee amount")
    time: datetime | None = Field(default=None, description="Trade execution time")
