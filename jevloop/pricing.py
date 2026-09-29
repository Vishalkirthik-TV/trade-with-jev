"""
pricing.py — Avellaneda-Stoikov reservation price and half-spread.

All arithmetic. No Jev calls here.
Spread is worked out in basis points of mid so it scales with price.
"""
from __future__ import annotations
import math


def avellaneda_stoikov(
    mid: float,
    position_qty: float,
    volatility: float,       # realised vol, fraction per second
    gamma: float = 0.1,      # risk aversion
    kappa: float = 1.5,      # order arrival rate
    T: float = 3600.0,       # session horizon in seconds
    t: float = 0.0,          # time elapsed in seconds
) -> tuple[float, float]:
    """
    Return (reservation_price, half_spread_bps).

    reservation_price: mid adjusted for inventory risk
    half_spread_bps:  half the quoted spread, in basis points of mid
    """
    tau = max(T - t, 1.0)  # time remaining, never zero

    # Reservation price
    r = mid - position_qty * gamma * (volatility ** 2) * tau

    # Half spread
    half_spread = (gamma * (volatility ** 2) * tau) + (2 / gamma) * math.log(1 + gamma / kappa)
    half_spread_bps = (half_spread / mid * 10000) if mid > 0 else 5.0

    return r, max(half_spread_bps, 1.0)


def quote_prices(
    mid: float,
    half_spread_bps: float,
    widen_factor: float = 1.0,
) -> tuple[float, float]:
    """Return (bid_price, ask_price) for posting."""
    half = mid * (half_spread_bps * widen_factor / 10000)
    return round(mid - half, 6), round(mid + half, 6)
