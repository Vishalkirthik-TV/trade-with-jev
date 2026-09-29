"""Tests for JevThrottle: one call at a time, rate-limit behaviour."""
import time
import pytest
from jevloop.client import JevThrottle, MockJevClient


def make_throttle(**kwargs):
    client = MockJevClient()
    defaults = dict(min_interval_s=0.1, min_gap_s=0.05,
                   material_move_bps=15.0, max_age_s=60.0)
    defaults.update(kwargs)
    return JevThrottle(client, **defaults)


STATE = {"mid": 50000.0, "position_qty": 0.0}


def test_first_call_always_fires():
    t = make_throttle()
    r = t.ask(STATE)
    assert r is not None


def test_reuses_within_interval():
    t = make_throttle(min_interval_s=10.0)
    r1 = t.ask(STATE)
    r2 = t.ask(STATE)
    assert r1 is r2  # same object reused


def test_material_move_triggers_new_call():
    t = make_throttle(min_interval_s=10.0, min_gap_s=0.0, material_move_bps=15.0)
    r1 = t.ask({"mid": 50000.0, "position_qty": 0.0})
    time.sleep(0.01)
    # Move 100 bps
    r2 = t.ask({"mid": 50500.0, "position_qty": 0.0})
    assert r1 is not r2


def test_force_fires_immediately():
    t = make_throttle(min_interval_s=10.0)
    r1 = t.ask(STATE)
    r2 = t.ask(STATE, force=True)
    assert r1 is not r2
