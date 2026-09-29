"""
policy.py — compose_action(): turns seven Jev answers into one action.

Actions: KILL | PULL_QUOTES | WIDEN | QUOTE_BOTH_SIDES | QUOTE_WIDE | STAND_DOWN

Never calls Jev. Uses strategy.py's thresholds, then calls strategy.py's hook.
"""
from __future__ import annotations
from jevloop.battery import BatteryResult
import jevloop.strategy as strategy


ACTIONS = frozenset([
    "KILL", "PULL_QUOTES", "WIDEN", "QUOTE_BOTH_SIDES", "QUOTE_WIDE", "STAND_DOWN"
])


def compose_action(battery: BatteryResult, state: dict) -> str:
    """
    Turn seven battery answers into one action using strategy.py's thresholds,
    then pass through strategy.py's apply_strategy hook.
    """
    # 1. Hard KILL: extreme drawdown or chaotic + toxic
    drawdown_pct = state.get("drawdown_pct", 0.0)
    if drawdown_pct >= 1.8:  # approaching max_drawdown_fraction * 100
        action = "KILL"
        return strategy.apply_strategy(action, battery, state)

    # 2. Toxic flow → pull quotes
    if battery.toxic_flow >= strategy.TOXIC_FLOW_THRESHOLD:
        action = "PULL_QUOTES"
        return strategy.apply_strategy(action, battery, state)

    # 3. Inventory pressure → stand down
    if battery.inventory_pressure >= strategy.INVENTORY_PRESSURE_THRESHOLD:
        action = "STAND_DOWN"
        return strategy.apply_strategy(action, battery, state)

    # 4. Chaotic regime → reduce
    if battery.regime == "chaotic" and battery.confidence >= strategy.REGIME_CHAOTIC_THRESHOLD:
        action = "WIDEN"
        return strategy.apply_strategy(action, battery, state)

    # 5. Liquidity stress → widen
    if battery.liquidity_stress >= strategy.LIQUIDITY_STRESS_THRESHOLD:
        action = "WIDEN"
        return strategy.apply_strategy(action, battery, state)

    # 6. Poor execution health → widen
    if battery.execution_health < strategy.EXECUTION_HEALTH_MIN:
        action = "WIDEN"
        return strategy.apply_strategy(action, battery, state)

    # 7. Good conditions: quote side based on quote environment
    if battery.quote_environment >= strategy.QUOTE_ENV_MIN:
        action = "QUOTE_BOTH_SIDES"
    else:
        action = "QUOTE_WIDE"

    return strategy.apply_strategy(action, battery, state)
