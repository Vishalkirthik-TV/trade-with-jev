"""
risk.py — nine hard risk limits, checked before every order.

Never calls Jev. Never delegated. Runs after strategy.py's hook.
A strategy can add caution but never raise these caps.
"""
from __future__ import annotations
from jevloop import limits


class RiskVeto(Exception):
    """Raised when a risk limit would be breached."""
    pass


def check_order(
    side: str,                   # "buy" or "sell"
    notional_usd: float,
    position_qty: float,
    position_notional_usd: float,
    working_buy_count: int,
    spread_bps: float,
    mid: float,
    session_start_equity: float,
    current_equity: float,
    inventory_fraction: float,
    mock: bool = False,
) -> None:
    """
    Raise RiskVeto if any hard limit would be breached.
    All nine limits checked, no delegation to Jev.
    """
    # 1. Mock client → never place orders
    if mock:
        raise RiskVeto("Mock client active — orders disabled.")

    # 2. Order notional floor
    if notional_usd < limits.MIN_ORDER_NOTIONAL_USD:
        raise RiskVeto(
            f"Order notional ${notional_usd:.2f} below floor ${limits.MIN_ORDER_NOTIONAL_USD}."
        )

    # 3. Order notional ceiling
    if notional_usd > limits.MAX_ORDER_NOTIONAL_USD:
        raise RiskVeto(
            f"Order notional ${notional_usd:.2f} exceeds cap ${limits.MAX_ORDER_NOTIONAL_USD}."
        )

    # 4. Position notional cap
    projected_position = position_notional_usd + (notional_usd if side == "buy" else -notional_usd)
    if abs(projected_position) > limits.MAX_POSITION_NOTIONAL_USD:
        raise RiskVeto(
            f"Projected position ${abs(projected_position):.2f} exceeds cap "
            f"${limits.MAX_POSITION_NOTIONAL_USD}."
        )

    # 5. Working buy count
    if side == "buy" and working_buy_count >= limits.MAX_WORKING_BUYS:
        raise RiskVeto(
            f"Already have {working_buy_count} working buys (cap {limits.MAX_WORKING_BUYS})."
        )

    # 6. Spread too wide to quote profitably
    if spread_bps > limits.MAX_SPREAD_BPS:
        raise RiskVeto(
            f"Spread {spread_bps:.1f} bps exceeds max {limits.MAX_SPREAD_BPS} bps."
        )

    # 7. Drawdown cap
    if session_start_equity > 0:
        drawdown = (session_start_equity - current_equity) / session_start_equity
        if drawdown >= limits.MAX_DRAWDOWN_FRACTION:
            raise RiskVeto(
                f"Drawdown {drawdown*100:.2f}% hit cap {limits.MAX_DRAWDOWN_FRACTION*100:.0f}%."
            )

    # 8. Inventory imbalance
    if inventory_fraction > limits.MAX_INVENTORY_FRACTION:
        raise RiskVeto(
            f"Inventory fraction {inventory_fraction:.2f} exceeds cap "
            f"{limits.MAX_INVENTORY_FRACTION}."
        )

    # 9. Spread below minimum (don't quote below this)
    if spread_bps < limits.MIN_SPREAD_BPS and side == "buy":
        raise RiskVeto(
            f"Spread {spread_bps:.1f} bps below minimum {limits.MIN_SPREAD_BPS} bps."
        )
