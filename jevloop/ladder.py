"""
ladder.py — five-rung fallback ladder for the "24/7" promise.

RUN          healthy + high confidence (Jev current, no limits near)
REDUCE       healthy + low confidence (Jev current, but uncertain)
HOLD_LATE    loop took too long (stale state, never quote on it)
RULES_ONLY   Jev unavailable (deterministic fallback, no model)
KILL         hard limit breached (cancel own orders, close position, stop)
"""
from __future__ import annotations
import time
from typing import Optional
from jevloop.battery import BatteryResult
from jevloop import limits


RUNGS = ["RUN", "REDUCE", "HOLD_LATE", "RULES_ONLY", "KILL"]


def evaluate(
    battery: Optional[BatteryResult],
    state: dict,
    tick_start: float,
    tick_budget_s: float = 5.0,
    jev_error: bool = False,
) -> str:
    """Return the current ladder rung."""
    # KILL: drawdown breached
    drawdown_pct = state.get("drawdown_pct", 0.0)
    if drawdown_pct >= limits.MAX_DRAWDOWN_FRACTION * 100:
        return "KILL"

    # HOLD_LATE: tick took too long
    elapsed = time.time() - tick_start
    if elapsed > tick_budget_s:
        return "HOLD_LATE"

    # RULES_ONLY: Jev unavailable or stale
    if battery is None or jev_error or battery.is_stale(limits.MAX_JUDGMENT_AGE_S):
        return "RULES_ONLY"

    # RUN / REDUCE based on confidence
    if battery.confidence >= 0.55:
        return "RUN"
    return "REDUCE"
