from pydantic import BaseModel, ConfigDict, Field


class Asset(BaseModel):
    """An asset metadata record."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Asset UUID")
    name: str = Field(default="", description="Asset name")
    symbol: str = Field(default="", description="Asset symbol")


class AssetEnvelope(BaseModel):
    """Single asset response envelope."""

    model_config = ConfigDict(extra="ignore")

    data: Asset
