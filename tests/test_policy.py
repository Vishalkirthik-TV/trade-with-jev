"""Tests for policy thresholds and compose_action."""
import pytest
from unittest.mock import patch
from jevloop.battery import BatteryResult
from jevloop.policy import compose_action


def make_battery(**kwargs):
    defaults = dict(
        regime="mean_reverting", direction="neutral",
        toxic_flow=0.1, liquidity_stress=0.1,
        quote_environment=0.8, inventory_pressure=0.1,
        execution_health=0.9, confidence=0.8,
        latency_ms=50, model="test", mock=False,
    )
    defaults.update(kwargs)
    return BatteryResult(**defaults)


STATE_OK = {"drawdown_pct": 0.0, "mid": 50000.0, "spread_bps": 10.0,
            "position_qty": 0.0, "position_notional_usd": 0.0}


def test_toxic_flow_pulls_quotes():
    b = make_battery(toxic_flow=0.9)
    assert compose_action(b, STATE_OK) == "PULL_QUOTES"


def test_inventory_pressure_stands_down():
    b = make_battery(inventory_pressure=0.9)
    assert compose_action(b, STATE_OK) == "STAND_DOWN"


def test_good_conditions_quote_both_sides():
    b = make_battery()
    assert compose_action(b, STATE_OK) == "QUOTE_BOTH_SIDES"


def test_poor_quote_env_quote_wide():
    b = make_battery(quote_environment=0.2)
    assert compose_action(b, STATE_OK) == "QUOTE_WIDE"


def test_drawdown_kill():
    state = dict(STATE_OK, drawdown_pct=2.0)
    b = make_battery()
    assert compose_action(b, state) == "KILL"


def test_chaotic_regime_widens():
    b = make_battery(regime="chaotic", confidence=0.9)
    assert compose_action(b, STATE_OK) == "WIDEN"
