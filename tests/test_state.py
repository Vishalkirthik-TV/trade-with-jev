"""Tests for the deterministic state snapshot maths."""
from jevloop.state import build_state


def _state(**kwargs):
    defaults = dict(
        bid=49990.0, ask=50010.0, last_trade=50000.0,
        bid_size=1.5, ask_size=1.0,
        position_qty=0.0, position_avg_px=0.0,
        session_start_equity=10000.0, current_equity=10000.0,
        session_trades=[], bars_1m=[], symbol="BTC/USD",
    )
    defaults.update(kwargs)
    return build_state(**defaults)


def test_mid_price():
    s = _state(bid=49990, ask=50010)
    assert s["mid"] == 50000.0


def test_spread_bps():
    s = _state(bid=49990, ask=50010)
    # spread = 20, mid = 50000, bps = 20/50000*10000 = 4.0
    assert abs(s["spread_bps"] - 4.0) < 0.01


def test_book_imbalance_positive():
    s = _state(bid_size=2.0, ask_size=1.0)
    assert s["book_imbalance"] > 0


def test_zero_drawdown():
    s = _state(session_start_equity=10000, current_equity=10000)
    assert s["drawdown_pct"] == 0.0


def test_positive_drawdown():
    s = _state(session_start_equity=10000, current_equity=9800)
    assert abs(s["drawdown_pct"] - 2.0) < 0.01


def test_flat_position_side():
    s = _state(position_qty=0.0)
    assert s["position_side"] == "flat"


def test_long_position_side():
    s = _state(position_qty=0.5)
    assert s["position_side"] == "long"
