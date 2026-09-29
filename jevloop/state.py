"""
state.py — deterministic state snapshot.

Computes exact arithmetic only: mid-price, spread, book imbalance,
inventory, drawdown, session VWAP. No fuzzy judgments here.
"""
from __future__ import annotations
import time
from typing import Optional


def build_state(
    bid: float,
    ask: float,
    last_trade: float,
    bid_size: Optional[float],
    ask_size: Optional[float],
    position_qty: float,
    position_avg_px: float,
    session_start_equity: float,
    current_equity: float,
    session_trades: list,
    bars_1m: list,
    symbol: str,
) -> dict:
    """Return a deterministic state dict suitable for the Jev battery prompt."""
    mid = (bid + ask) / 2.0
    spread = ask - bid
    spread_bps = (spread / mid * 10000) if mid > 0 else 0.0

    # Book imbalance: positive means more bid size (buy pressure)
    if bid_size and ask_size and (bid_size + ask_size) > 0:
        book_imbalance = (bid_size - ask_size) / (bid_size + ask_size)
    else:
        book_imbalance = None

    # Session VWAP
    if session_trades:
        total_notional = sum(t["price"] * t["qty"] for t in session_trades)
        total_qty = sum(t["qty"] for t in session_trades)
        session_vwap = total_notional / total_qty if total_qty > 0 else None
    else:
        session_vwap = None

    # Drawdown from session-start equity
    if session_start_equity > 0:
        drawdown_pct = (session_start_equity - current_equity) / session_start_equity * 100
    else:
        drawdown_pct = 0.0

    # Position notional
    position_notional = abs(position_qty * mid) if mid > 0 else 0.0
    position_side = "long" if position_qty > 0 else ("flat" if position_qty == 0 else "short")

    # Recent price change from 1-minute bars
    price_change_1m = None
    volatility_1m = None
    if bars_1m and len(bars_1m) >= 2:
        closes = [b["close"] for b in bars_1m[-20:]]
        price_change_1m = (closes[-1] - closes[-2]) / closes[-2] * 100 if closes[-2] > 0 else None
        if len(closes) >= 5:
            import statistics
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            volatility_1m = statistics.stdev(returns) * 100 if len(returns) > 1 else None

    return {
        "symbol": symbol,
        "mid": round(mid, 6),
        "bid": round(bid, 6),
        "ask": round(ask, 6),
        "spread_bps": round(spread_bps, 2),
        "book_imbalance": round(book_imbalance, 4) if book_imbalance is not None else None,
        "last_trade": round(last_trade, 6),
        "position_qty": round(position_qty, 8),
        "position_side": position_side,
        "position_avg_px": round(position_avg_px, 6) if position_avg_px else None,
        "position_notional_usd": round(position_notional, 2),
        "session_vwap": round(session_vwap, 6) if session_vwap else None,
        "drawdown_pct": round(drawdown_pct, 4),
        "price_change_1m_pct": round(price_change_1m, 4) if price_change_1m is not None else None,
        "volatility_1m_pct": round(volatility_1m, 4) if volatility_1m is not None else None,
        "ts": time.time(),
    }
