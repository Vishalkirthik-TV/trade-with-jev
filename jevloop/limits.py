"""Hard risk caps — never overridable by strategy.py."""

# Maximum single-order notional in USD
MAX_ORDER_NOTIONAL_USD = 50.0

# Maximum total position notional in USD
MAX_POSITION_NOTIONAL_USD = 200.0

# Maximum drawdown from session-start equity (fraction)
MAX_DRAWDOWN_FRACTION = 0.02  # 2%

# Maximum number of working (open) buy orders at once
MAX_WORKING_BUYS = 3

# Maximum spread we're willing to post (basis points of mid)
MAX_SPREAD_BPS = 150.0

# Minimum spread (below this we widen, not narrow further)
MIN_SPREAD_BPS = 1.0

# Maximum inventory imbalance (fraction of max position)
MAX_INVENTORY_FRACTION = 0.8

# Maximum Jev judgment age before we drop to RULES_ONLY (seconds)
MAX_JUDGMENT_AGE_S = 60

# Minimum order notional (Alpaca floor)
MIN_ORDER_NOTIONAL_USD = 1.0

# Target order notional for normal quotes
NOTIONAL_USD = 20.0
