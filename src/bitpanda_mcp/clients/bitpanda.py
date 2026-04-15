from typing import Any

import httpx

from bitpanda_mcp.clients.base import BaseClient
from bitpanda_mcp.models.assets import AssetData, AssetResponse
from bitpanda_mcp.models.market import Ticker, TickerEntry
from bitpanda_mcp.models.transactions import Trade, Transaction
from bitpanda_mcp.models.wallets import FiatWallet, Wallet


class BitpandaClient(BaseClient):
    """Client for the Bitpanda Public API v1."""

    def __init__(self, http: httpx.AsyncClient, api_key: str) -> None:
        super().__init__(http, {"X-Api-Key": api_key})

    # --- Assets ---

    async def get_asset(self, asset_id: str) -> AssetData:
        """Fetch a single asset by UUID."""
        raw = await self._get(f"/v1/assets/{asset_id}")
        return AssetResponse.model_validate(raw).data

    async def list_assets(
        self,
        *,
        asset_type: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch paginated list of assets, optionally filtered by type."""
        params: dict[str, Any] = {}
        if asset_type:
            params["asset_groups"] = asset_type
        return await self._paginate_all("/v1/assets", params=params, page_size=page_size, limit=limit)

    # --- Crypto Wallets ---

    async def list_wallets(
        self,
        *,
        asset_id: str | None = None,
        index_asset_id: str | None = None,
        last_credited_at_from: str | None = None,
        last_credited_at_to: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Wallet]:
        """Fetch paginated list of crypto wallets."""
        params: dict[str, Any] = {}
        if asset_id:
            params["asset_id"] = asset_id
        if index_asset_id:
            params["index_asset_id"] = index_asset_id
        if last_credited_at_from:
            params["last_credited_at_from_including"] = last_credited_at_from
        if last_credited_at_to:
            params["last_credited_at_to_excluding"] = last_credited_at_to
        raw_items = await self._paginate_all("/v1/wallets/", params=params, page_size=page_size, limit=limit)
        return [Wallet.model_validate(item) for item in raw_items]

    # --- Fiat Wallets ---

    async def list_fiat_wallets(self) -> list[FiatWallet]:
        """Fetch all fiat currency wallets (EUR, USD, GBP, CHF)."""
        raw = await self._get("/v1/fiatwallets")
        items = raw.get("data", [])
        return [FiatWallet.model_validate(item) for item in items]

    async def list_fiat_transactions(
        self,
        *,
        fiat_wallet_id: str | None = None,
        status: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch fiat wallet transactions."""
        params: dict[str, Any] = {}
        if fiat_wallet_id:
            params["fiat_wallet_id"] = fiat_wallet_id
        if status:
            params["status"] = status
        return await self._paginate_all(
            "/v1/fiatwallets/transactions", params=params, page_size=page_size, limit=limit
        )

    # --- Crypto Wallet Transactions ---

    async def list_crypto_transactions(
        self,
        *,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch crypto wallet transactions (deposits, withdrawals, etc.)."""
        return await self._paginate_all("/v1/wallets/transactions", page_size=page_size, limit=limit)

    # --- General Transactions ---

    async def list_transactions(
        self,
        *,
        wallet_id: str | None = None,
        flow: str | None = None,
        asset_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Transaction]:
        """Fetch paginated list of transactions with optional filters."""
        params: dict[str, Any] = {}
        if wallet_id:
            params["wallet_id"] = wallet_id
        if flow:
            params["flow"] = flow
        if asset_id:
            params["asset_id"] = asset_id
        if from_date:
            params["from_including"] = from_date
        if to_date:
            params["to_excluding"] = to_date
        raw_items = await self._paginate_all(
            "/v1/transactions", params=params, page_size=page_size, limit=limit
        )
        return [Transaction.model_validate(item) for item in raw_items]

    # --- Trades ---

    async def list_trades(
        self,
        *,
        trade_type: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Trade]:
        """Fetch paginated list of trades from the dedicated /trades endpoint."""
        params: dict[str, Any] = {}
        if trade_type:
            params["type"] = trade_type
        raw_items = await self._paginate_all("/v1/trades", params=params, page_size=page_size, limit=limit)
        return [Trade.model_validate(item) for item in raw_items]

    # --- Ticker / Market Data ---

    async def fetch_ticker(self) -> Ticker:
        """Fetch the full ticker (all assets with prices).

        Uses the ticker API at /v1/ticker with cursor-based pagination.

        """
        raw_items = await self._paginate_all("/v1/ticker", page_size=100, cursor_param="cursor")
        entries = [TickerEntry.model_validate(item) for item in raw_items]
        return Ticker(entries)
