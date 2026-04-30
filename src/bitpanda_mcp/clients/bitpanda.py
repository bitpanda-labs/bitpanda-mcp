from typing import Any

import httpx

from bitpanda_mcp.clients.base import BaseClient
from bitpanda_mcp.models.assets import Asset, AssetEnvelope
from bitpanda_mcp.models.market import Ticker, TickerEntry
from bitpanda_mcp.models.transactions import Trade, Transaction
from bitpanda_mcp.models.wallets import Wallet


class BitpandaClient(BaseClient):
    """Client for the Bitpanda API v1."""

    def __init__(self, http: httpx.AsyncClient, api_key: str) -> None:
        super().__init__(http, {"X-Api-Key": api_key})

    # --- Wallets ---

    async def list_wallets(
        self,
        *,
        asset_id: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Wallet]:
        """Fetch all asset wallets."""
        params: dict[str, Any] = {}
        if asset_id:
            params["asset_id"] = asset_id
        raw_items = await self._paginate_all(
            "/v1/wallets/",
            params=params,
            cursor_param="after",
            page_size=page_size,
            limit=limit,
        )
        return [Wallet.model_validate(item) for item in raw_items]

    # --- Transactions ---

    async def list_transactions(
        self,
        *,
        wallet_id: str | None = None,
        flow: str | None = None,
        asset_id: str | None = None,
        from_including: str | None = None,
        to_excluding: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Transaction]:
        """Fetch asset transactions."""
        params: dict[str, Any] = {}
        if wallet_id:
            params["wallet_id"] = wallet_id
        if flow:
            params["flow"] = flow
        if asset_id:
            params["asset_id"] = asset_id
        if from_including:
            params["from_including"] = from_including
        if to_excluding:
            params["to_excluding"] = to_excluding
        raw_items = await self._paginate_all(
            "/v1/transactions",
            params=params,
            cursor_param="after",
            page_size=page_size,
            limit=limit,
        )
        return [Transaction.model_validate(item) for item in raw_items]

    # --- Trades ---

    async def list_trades(
        self,
        *,
        trade_type: str | None = None,
        asset_type: str | None = None,
        from_including: str | None = None,
        to_excluding: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Trade]:
        """Fetch buy and sell trades."""
        params: dict[str, Any] = {}
        if from_including:
            params["from_including"] = from_including
        if to_excluding:
            params["to_excluding"] = to_excluding

        ticker: Ticker | None = None
        trades: list[Trade] = []
        async for page in self._paginate_pages(
            "/v1/transactions",
            params=params,
            cursor_param="after",
            page_size=page_size,
        ):
            for raw_tx in page.data:
                tx = Transaction.model_validate(raw_tx)
                if not tx.is_trade or (trade_type and tx.operation_type != trade_type):
                    continue
                if ticker is None:
                    ticker = await self.fetch_ticker()
                ticker_entry = ticker.get_by_asset_id(tx.asset_id)
                if asset_type and (not ticker_entry or ticker_entry.type != asset_type):
                    continue
                trades.append(
                    Trade(
                        transaction_id=tx.transaction_id,
                        trade_id=tx.trade_id,
                        type=tx.operation_type,
                        asset_id=tx.asset_id,
                        asset_symbol=ticker_entry.symbol if ticker_entry else "",
                        asset_name=ticker_entry.name if ticker_entry else "",
                        asset_type=ticker_entry.type if ticker_entry else "",
                        asset_amount=tx.asset_amount,
                        fee_amount=tx.fee_amount,
                        credited_at=tx.credited_at,
                        price_eur=ticker_entry.price_eur if ticker_entry else None,
                    )
                )

                if limit and len(trades) >= limit:
                    return trades

        return trades

    # --- Ticker / Market Data ---

    async def fetch_ticker(self) -> Ticker:
        """Fetch the public ticker."""
        raw_items = await self._paginate_all("/v1/ticker", cursor_param="cursor", page_size=500)
        entries: list[TickerEntry] = []
        for item in raw_items:
            entry = TickerEntry.model_validate(item)
            entries.append(entry)
        return Ticker(entries)

    # --- Assets ---

    async def get_asset(self, asset_id: str) -> Asset:
        """Fetch one asset by ID."""
        raw = await self._get(f"/v1/assets/{asset_id}")
        return AssetEnvelope.model_validate(raw).data
