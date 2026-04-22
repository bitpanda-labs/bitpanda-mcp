from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Trade(BaseModel):
    """A trade from ``/v1/trades`` after flattening the JSON:API envelope."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Trade UUID")
    status: str = Field(default="", description="Trade status, e.g. finished")
    type: str = Field(default="", description="buy or sell")
    cryptocoin_id: str = Field(default="", description="Numeric asset ID")
    cryptocoin_symbol: str = Field(default="", description="Asset symbol, e.g. BTC")
    fiat_id: str = Field(default="", description="Numeric fiat ID")
    amount_fiat: str = Field(default="0", description="Fiat amount as string-decimal")
    amount_cryptocoin: str = Field(default="0", description="Crypto amount as string-decimal")
    price: str = Field(default="0", description="Price per unit in fiat")
    fee: str = Field(default="0", description="Fee amount")
    time: Any = Field(default=None, description="Trade execution timestamp as returned by the API")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fee(cls, data: Any) -> Any:
        # /v1/trades returns fee as a nested JSON:API object
        # {type: "fee", attributes: {fee_amount: ...}}; flatten to the amount string.
        if isinstance(data, dict) and isinstance(data.get("fee"), dict):
            fee_attrs = data["fee"].get("attributes", {})
            data = {**data, "fee": str(fee_attrs.get("fee_amount", "0"))}
        return data
