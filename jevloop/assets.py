"""Resolve any symbol into a trading spec for Alpaca."""
from __future__ import annotations
import re

CRYPTO_ASSETS = {
    "BTC/USD", "ETH/USD", "PAXG/USD", "SOL/USD", "AVAX/USD",
    "LINK/USD", "LTC/USD", "BCH/USD", "DOGE/USD", "SHIB/USD",
    "UNI/USD", "AAVE/USD", "DOT/USD", "MATIC/USD",
}

EQUITY_ASSETS = {
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META",
    "SPY", "QQQ", "IWM", "GLD", "SLV", "TLT", "XLF",
    "NFLX", "AMD", "INTC", "BA", "JPM", "GS",
}

CRYPTO_NOTIONAL_FLOORS = {
    "BTC/USD": 1.0, "ETH/USD": 1.0, "PAXG/USD": 1.0,
}
EQUITY_NOTIONAL_FLOOR = 1.0

CRYPTO_QTY_PRECISION = {
    "BTC/USD": 8, "ETH/USD": 6, "PAXG/USD": 4,
}


def resolve(symbol: str) -> dict:
    """Return a spec dict for the given symbol."""
    sym = symbol.upper().strip()

    # Detect crypto (contains /)
    if "/" in sym:
        if sym not in CRYPTO_ASSETS:
            raise ValueError(
                f"Unknown crypto pair '{sym}'. "
                f"Supported: {sorted(CRYPTO_ASSETS)}"
            )
        return {
            "symbol": sym,
            "kind": "crypto",
            "alpaca_symbol": sym,
            "notional_floor": CRYPTO_NOTIONAL_FLOORS.get(sym, 1.0),
            "qty_precision": CRYPTO_QTY_PRECISION.get(sym, 6),
            "shorting": False,
            "market_hours_only": False,
            "quote_endpoint": "crypto",
            "bars_endpoint": "crypto",
        }

    # Equity
    return {
        "symbol": sym,
        "kind": "equity",
        "alpaca_symbol": sym,
        "notional_floor": EQUITY_NOTIONAL_FLOOR,
        "qty_precision": 0,  # whole shares
        "shorting": False,
        "market_hours_only": True,
        "quote_endpoint": "equity",
        "bars_endpoint": "equity",
    }
