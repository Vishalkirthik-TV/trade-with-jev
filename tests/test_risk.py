"""Tests for the nine hard risk limits."""
import pytest
from jevloop.risk import check_order, RiskVeto


BASE = dict(
    notional_usd=20.0, position_qty=0.0, position_notional_usd=0.0,
    working_buy_count=0, spread_bps=10.0, mid=50000.0,
    session_start_equity=10000.0, current_equity=10000.0,
    inventory_fraction=0.1, mock=False,
)


def test_mock_blocks_all_orders():
    with pytest.raises(RiskVeto, match="Mock"):
        check_order(side="buy", **{**BASE, "mock": True})


def test_notional_too_large():
    with pytest.raises(RiskVeto, match="cap"):
        check_order(side="buy", **{**BASE, "notional_usd": 999.0})


def test_position_cap():
    with pytest.raises(RiskVeto, match="cap"):
        check_order(side="buy", **{**BASE, "position_notional_usd": 190.0})


def test_working_buy_cap():
    with pytest.raises(RiskVeto, match="working buys"):
        check_order(side="buy", **{**BASE, "working_buy_count": 3})


def test_drawdown_cap():
    with pytest.raises(RiskVeto, match="Drawdown"):
        check_order(side="buy", **{**BASE, "current_equity": 9700.0})


def test_notional_floor():
    with pytest.raises(RiskVeto, match="floor"):
        check_order(side="buy", **{**BASE, "notional_usd": 0.5})


def test_valid_order_passes():
    check_order(side="buy", **BASE)  # should not raise
