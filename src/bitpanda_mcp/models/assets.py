from pydantic import BaseModel, ConfigDict, Field


class AssetData(BaseModel):
    """Core asset fields."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique asset identifier (UUID)")
    name: str = Field(description="Human-readable asset name")
    symbol: str = Field(description="Ticker symbol (e.g. BTC, ETH)")


class AssetResponse(BaseModel):
    """Single-asset API response wrapper."""

    data: AssetData
