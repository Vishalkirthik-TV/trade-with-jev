"""
execution/alpaca.py — Alpaca paper (default) and live execution.

Paper by default. Live trading requires all three simultaneously:
  1. --live flag
  2. JEV_LOOP_ALLOW_LIVE=i-understand-the-risk in environment
  3. User types the exact confirmation phrase at startup

Never places equity orders while the market is closed.
Never touches orders placed by other sessions.
"""
from __future__ import annotations
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests

PAPER_BASE = "https://paper-api.alpaca.markets"
LIVE_BASE  = "https://api.alpaca.markets"

DATA_BASE_CRYPTO = "https://data.alpaca.markets/v1beta3/crypto/us"
DATA_BASE_EQUITY = "https://data.alpaca.markets/v2"

MARKET_OPEN_HOUR_UTC  = 14   # 9:30 ET = 14:30 UTC
MARKET_CLOSE_HOUR_UTC = 21   # 4:00 PM ET = 21:00 UTC


def _is_equity_market_open() -> bool:
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    open_min  = MARKET_OPEN_HOUR_UTC * 60 + 30
    close_min = MARKET_CLOSE_HOUR_UTC * 60
    current_min = now.hour * 60 + now.minute
    return open_min <= current_min < close_min


class AlpacaClient:
    def __init__(self, api_key: str, secret_key: str, live: bool = False):
        if live:
            allow = os.environ.get("JEV_LOOP_ALLOW_LIVE", "")
            if allow != "i-understand-the-risk":
                raise RuntimeError(
                    "Live trading refused: JEV_LOOP_ALLOW_LIVE must be "
                    "'i-understand-the-risk' in the environment."
                )
        self.base = LIVE_BASE if live else PAPER_BASE
        self.live = live
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }
        self._order_ids: list[str] = []  # track only our own orders

    def _get(self, url: str, params: dict = None) -> dict:
        r = requests.get(url, headers=self._headers, params=params, timeout=8)
        r.raise_for_status()
        return r.json()

    def _post(self, url: str, body: dict) -> dict:
        r = requests.post(url, headers=self._headers, json=body, timeout=8)
        r.raise_for_status()
        return r.json()

    def _delete(self, url: str) -> None:
        r = requests.delete(url, headers=self._headers, timeout=8)
        # 404 is fine (already filled/cancelled)
        if r.status_code not in (200, 204, 404):
            r.raise_for_status()

    # ── Quote / data ──────────────────────────────────────────────────────────

    def get_quote(self, symbol: str, kind: str) -> dict:
        """Return latest quote: {bid, ask, bid_size, ask_size, last_trade}."""
        if kind == "crypto":
            url = f"{DATA_BASE_CRYPTO}/latest/quotes"
            data = self._get(url, {"symbols": symbol})
            q = data["quotes"][symbol]
            return {
                "bid": float(q["bp"]),
                "ask": float(q["ap"]),
                "bid_size": float(q.get("bs", 0)),
                "ask_size": float(q.get("as", 0)),
                "last_trade": float(q.get("bp", q["bp"])),
            }
        else:
            url = f"{DATA_BASE_EQUITY}/stocks/{symbol}/quotes/latest"
            data = self._get(url)
            q = data["quote"]
            return {
                "bid": float(q["bp"]),
                "ask": float(q["ap"]),
                "bid_size": float(q.get("bs", 0)),
                "ask_size": float(q.get("as", 0)),
                "last_trade": float(q.get("bp", q["bp"])),
            }

    def get_bars_1m(self, symbol: str, kind: str, limit: int = 30) -> list:
        """Return recent 1-minute bars: [{open,high,low,close,volume,ts}]."""
        if kind == "crypto":
            url = f"{DATA_BASE_CRYPTO}/bars"
            data = self._get(url, {"symbols": symbol, "timeframe": "1Min", "limit": limit})
            bars = data.get("bars", {}).get(symbol, [])
        else:
            url = f"{DATA_BASE_EQUITY}/stocks/{symbol}/bars"
            data = self._get(url, {"timeframe": "1Min", "limit": limit})
            bars = data.get("bars", [])
        return [
            {"open": b["o"], "high": b["h"], "low": b["l"], "close": b["c"],
             "volume": b.get("v", 0), "ts": b["t"]}
            for b in bars
        ]

    # ── Account ───────────────────────────────────────────────────────────────

    def get_account(self) -> dict:
        data = self._get(f"{self.base}/v2/account")
        return {
            "equity": float(data["equity"]),
            "cash": float(data["cash"]),
            "buying_power": float(data["buying_power"]),
        }

    def get_position(self, symbol: str) -> dict:
        """Return {qty, avg_px, side, notional}. Returns zeros if flat."""
        alpaca_sym = symbol.replace("/", "")
        try:
            data = self._get(f"{self.base}/v2/positions/{alpaca_sym}")
            qty = float(data["qty"])
            return {
                "qty": qty,
                "avg_px": float(data["avg_entry_price"]),
                "side": data["side"],
                "notional": abs(qty * float(data["current_price"])),
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {"qty": 0.0, "avg_px": 0.0, "side": "flat", "notional": 0.0}
            raise

    def get_working_orders(self, symbol: str) -> list:
        """Return open orders for this symbol that we placed."""
        alpaca_sym = symbol.replace("/", "")
        data = self._get(f"{self.base}/v2/orders", {"status": "open", "symbols": alpaca_sym})
        return [o for o in data if o["id"] in self._order_ids]

    # ── Orders ────────────────────────────────────────────────────────────────

    def place_limit_order(
        self, symbol: str, side: str, notional_usd: float, limit_px: float,
        kind: str, time_in_force: str = "gtc"
    ) -> Optional[str]:
        """Place a limit order. Returns order_id or None on dry-run."""
        alpaca_sym = symbol.replace("/", "")

        if kind == "equity" and not _is_equity_market_open():
            print(f"  ⏸  Market closed for {symbol} — order not placed.")
            return None

        qty = round(notional_usd / limit_px, 8 if kind == "crypto" else 0)
        if qty <= 0:
            return None

        # Round down for sells to avoid "insufficient qty" errors
        if side == "sell":
            qty = round(qty * 0.999, 8 if kind == "crypto" else 0)

        body = {
            "symbol": alpaca_sym,
            "qty": str(qty),
            "side": side,
            "type": "limit",
            "limit_price": str(round(limit_px, 2)),
            "time_in_force": time_in_force,
        }
        data = self._post(f"{self.base}/v2/orders", body)
        order_id = data["id"]
        self._order_ids.append(order_id)
        return order_id

    def close_position(self, symbol: str) -> None:
        """Market-close the full position for this symbol."""
        alpaca_sym = symbol.replace("/", "")
        try:
            self._delete(f"{self.base}/v2/positions/{alpaca_sym}")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                pass  # already flat
            else:
                raise

    def cancel_our_orders(self, symbol: str) -> int:
        """Cancel only the orders we placed this run. Returns count cancelled."""
        count = 0
        for oid in list(self._order_ids):
            try:
                self._delete(f"{self.base}/v2/orders/{oid}")
                count += 1
            except Exception:
                pass
        self._order_ids.clear()
        return count
