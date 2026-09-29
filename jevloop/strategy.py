"""
strategy.py — THE FILE YOU EDIT.

Seven tunable thresholds that compose_action() reads, plus apply_strategy(),
a hook called on every tick after the action is composed, free to change or
veto it outright. The shipped default matches exactly what the video ran:
change nothing here and nothing changes.

Hard risk caps live in limits.py and are never edited here.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jevloop.battery import BatteryResult

# ── Seven tunable thresholds ──────────────────────────────────────────────────

# Minimum Jev confidence (0–1) to act on a directional signal
DIRECTION_CONFIDENCE_MIN = 0.65

# Toxic-flow score above this → PULL_QUOTES
TOXIC_FLOW_THRESHOLD = 0.70

# Liquidity-stress score above this → WIDEN
LIQUIDITY_STRESS_THRESHOLD = 0.60

# Inventory-pressure score above this → STAND_DOWN (we're too long/short)
INVENTORY_PRESSURE_THRESHOLD = 0.75

# Execution-health score below this → WIDEN quotes
EXECUTION_HEALTH_MIN = 0.40

# Regime chaotic score above this → REDUCE
REGIME_CHAOTIC_THRESHOLD = 0.65

# Quote-environment score below this → QUOTE_WIDE instead of QUOTE_BOTH_SIDES
QUOTE_ENV_MIN = 0.45


# ── Strategy hook ─────────────────────────────────────────────────────────────

def apply_strategy(action: str, battery: "BatteryResult", state: dict) -> str:
    """
    Last look before an action reaches the risk engine.

    Parameters
    ----------
    action : str
        Action proposed by compose_action(): one of KILL / PULL_QUOTES /
        WIDEN / QUOTE_BOTH_SIDES / QUOTE_WIDE / STAND_DOWN.
    battery : BatteryResult
        The seven Jev answers, typed and validated.
    state : dict
        The full deterministic state snapshot from state.py.

    Returns
    -------
    str
        The action to actually use — same as `action` to pass through,
        a different action string to override, or "STAND_DOWN" to veto.

    Notes
    -----
    This hook runs after compose_action() and before the risk engine.
    The risk engine still runs after this and can still veto. You cannot
    raise hard risk caps here; you can only add caution.
    """
    # Shipped default: pass through unchanged.
    return action
