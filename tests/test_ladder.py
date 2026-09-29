"""Tests for the five-rung fallback ladder."""
import time
import pytest
from jevloop.battery import BatteryResult
from jevloop.ladder import evaluate


def make_battery(confidence=0.8, age_s=0):
    b = BatteryResult(confidence=confidence)
    b.ts = time.time() - age_s
    return b


STATE = {"drawdown_pct": 0.0}


def test_run_on_healthy():
    b = make_battery(confidence=0.8)
    assert evaluate(b, STATE, time.time()) == "RUN"


def test_reduce_on_low_confidence():
    b = make_battery(confidence=0.4)
    assert evaluate(b, STATE, time.time()) == "REDUCE"


def test_rules_only_when_no_battery():
    assert evaluate(None, STATE, time.time()) == "RULES_ONLY"


def test_rules_only_when_stale():
    b = make_battery(age_s=120)
    assert evaluate(b, STATE, time.time()) == "RULES_ONLY"


def test_kill_on_drawdown():
    state = {"drawdown_pct": 2.5}
    b = make_battery()
    assert evaluate(b, state, time.time()) == "KILL"


def test_hold_late_on_slow_tick():
    b = make_battery()
    assert evaluate(b, STATE, time.time() - 5.0) == "HOLD_LATE"
