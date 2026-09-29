"""
split.py — the allow-list of Jev battery questions and the arithmetic guard.

The guard refuses any question that looks like a calculation so the
deterministic / probabilistic split is enforced in code, not by convention.
"""
from __future__ import annotations
import re

# The seven allowed question keys, in call order
BATTERY_KEYS = [
    "regime",
    "direction",
    "toxic_flow",
    "liquidity_stress",
    "quote_environment",
    "inventory_pressure",
    "execution_health",
]

_ARITHMETIC_MARKERS = (
    "calculate",
    "compute the",
    "what is the exact",
    "sum of",
    "average of",
    "mean of",
    "add up",
    "multiply",
    "divide by",
    "vwap",
    "moving average",
    "standard deviation",
    "variance of",
    "exact value",
    "precise value",
    "spread in bps",
    "mid price of",
    "what is the mid",
    "how much does",
)


def is_arithmetic(question: str) -> bool:
    """Return True if the question looks like a calculation."""
    q_lower = question.lower()
    return any(marker in q_lower for marker in _ARITHMETIC_MARKERS)


def validate_question(key: str, question: str) -> None:
    """Raise ValueError if the key is unknown or the question is arithmetic."""
    if key not in BATTERY_KEYS:
        raise ValueError(f"Unknown battery key '{key}'. Allowed: {BATTERY_KEYS}")
    if is_arithmetic(question):
        raise ValueError(
            f"Question '{question}' looks like arithmetic. "
            "Jev answers fuzzy judgments only; arithmetic belongs in state.py."
        )


def explain_split() -> None:
    """Print the deterministic vs probabilistic table to stdout."""
    rows = [
        ("mid-price, spread, book imbalance",    "state.py",    "—"),
        ("inventory, drawdown, session VWAP",    "state.py",    "—"),
        ("stop-losses, risk caps",               "limits.py",   "—"),
        ("order routing, sizing",                "risk.py",     "—"),
        ("regime (trending/reverting/chaotic)",  "—",           "battery.py"),
        ("direction (up / down / neutral)",      "—",           "battery.py"),
        ("toxic flow (toxic / noise)",           "—",           "battery.py"),
        ("liquidity stress (stressed / calm)",   "—",           "battery.py"),
        ("quote environment (good / degraded)",  "—",           "battery.py"),
        ("inventory pressure (high / low)",      "—",           "battery.py"),
        ("execution health (optimal / degrad.)", "—",           "battery.py"),
        ("compose action from answers",          "policy.py",   "—"),
        ("strategy hook / veto",                 "strategy.py", "—"),
    ]
    print("\nTHE SPLIT")
    print("-" * 72)
    print(f"{'Judgment / Metric':<40} {'Deterministic':^15} {'Jev':^10}")
    print("-" * 72)
    for label, det, prob in rows:
        print(f"{label:<40} {det:^15} {prob:^10}")
    print("-" * 72)
    print("Jev: seven typed questions, one call, no arithmetic, no 'what should I do'.\n")
