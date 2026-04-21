from typing import Any

import httpx

from bitpanda_mcp.clients.base import BaseClient, flatten_jsonapi
from bitpanda_mcp.models.market import Ticker, TickerEntry
from bitpanda_mcp.models.transactions import Trade
from bitpanda_mcp.models.wallets import FiatWallet, Wallet


class BitpandaClient(BaseClient):
    """Client for the Bitpanda Public API v1."""

    def __init__(self, http: httpx.AsyncClient, api_key: str) -> None:
        super().__init__(http, {"X-Api-Key": api_key})

    # --- Crypto Wallets ---

    async def list_wallets(self) -> list[Wallet]:
        """Fetch all crypto wallets.

        ``/v1/wallets`` returns a flat ``{data: [...], last_user_action: {...}}``
        envelope (no pagination).
        """
        raw = await self._get("/v1/wallets")
        items = raw.get("data", []) if isinstance(raw, dict) else []
        return [Wallet.model_validate(flatten_jsonapi(item)) for item in items]

    # --- Fiat Wallets ---

    async def list_fiat_wallets(self) -> list[FiatWallet]:
        """Fetch all fiat currency wallets (EUR, USD, GBP, CHF, ...)."""
        raw = await self._get("/v1/fiatwallets")
        items = raw.get("data", []) if isinstance(raw, dict) else []
        return [FiatWallet.model_validate(flatten_jsonapi(item)) for item in items]

    # --- Fiat Wallet Transactions ---

    async def list_fiat_transactions(
        self,
        *,
        status: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch fiat wallet transactions."""
        params: dict[str, Any] = {}
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

    # --- Trades ---

    async def list_trades(
        self,
        *,
        trade_type: str | None = None,
        page_size: int = 25,
        limit: int = 0,
    ) -> list[Trade]:
        """Fetch paginated list of trades."""
        params: dict[str, Any] = {}
        if trade_type:
            params["type"] = trade_type
        raw_items = await self._paginate_all("/v1/trades", params=params, page_size=page_size, limit=limit)
        return [Trade.model_validate(item) for item in raw_items]

    # --- Ticker / Market Data ---

    async def fetch_ticker(self) -> Ticker:
        """Fetch the public ticker.

        Response is a flat dict: ``{symbol: {currency: price, ...}, ...}``.
        Only symbols that quote EUR are kept.
        """
        raw = await self._get("/v1/ticker")
        if not isinstance(raw, dict):
            return Ticker([])
        entries: list[TickerEntry] = []
        for symbol, prices in raw.items():
            if not isinstance(prices, dict):
                continue
            eur = prices.get("EUR")
            if eur is None:
                continue
            entries.append(TickerEntry(symbol=symbol, price_eur=str(eur)))
        return Ticker(entries)
