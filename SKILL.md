---
name: jev-loop
description: A 24/7 paper-trading loop for Alpaca, any crypto pair or US equity. Every tick computes a deterministic state snapshot, fires a seven-question judgment battery at TypeSafe's Jev decision model (the Vercel AI Gateway is the normal route, a direct TypeSafe key is a faster optional extra, or a labelled mock), composes an action from your own strategy.py thresholds, prices with Avellaneda-Stoikov, checks nine hard risk limits, and executes on Alpaca paper by default. Live trading exists behind a deliberately awkward three-gate opt-in, off unless all three are set. Includes a live HTML dashboard and a calibration report.
---

# jev-loop

Install location: `~/.claude/skills/jev-loop/`.
Framework: Roan (@RohOnChain), "How to Use Jev to Build a 24/7 HFT Trading System".

## The split

Deterministic layer (your code): exact arithmetic (mid-price, spread, book
imbalance), hard metrics (inventory, drawdown, session VWAP), safety and
policy (stop-losses, risk vetoes, routing orders to the book).

Probabilistic layer (Jev): fuzzy conditions (trending, mean reverting,
chaotic), order quality (is flow toxic or noise), execution health (is
the setup optimal or degrading). Seven typed questions, one call, one
latency, none of them arithmetic and none of them "what should I do."

```
uv run python -m jevloop explain-split
```

prints the full two-column table with the file that owns each row.

## Invocation

Natural language, or directly:

```
cd ~/.claude/skills/jev-loop
uv run python -m jevloop run --paper --ticks 60 --symbol BTC/USD
uv run python -m jevloop run --paper --mock            # force the mock client (never places orders)
uv run python -m jevloop run --paper --dry-execution   # real data and a real battery, no orders sent
uv run python -m jevloop run --paper --forever         # run continuously, Ctrl+C or `kill <pid>` to stop
uv run python -m jevloop run --paper --forever --bar 30m  # one decision per 30-minute bar close (1m/5m/15m/30m/1h)
uv run python -m jevloop validate-symbol AAPL          # resolve any symbol before running on it
uv run python -m jevloop explain-split                 # the deterministic vs probabilistic table
uv run python -m jevloop calibrate                     # Brier score + reliability table
uv run python -m jevloop serve                         # dashboard at http://127.0.0.1:8765
uv run python -m jevloop pause                         # same as Stop on the dashboard: no new orders
uv run python -m jevloop resume                        # same as Start on the dashboard
```

## Any asset

`--symbol` accepts any crypto pair (`BTC/USD`, `ETH/USD`, 24/7) or any US
equity ticker (`AAPL`, `SPY`, `TSLA`, `NVDA`, market hours only). The
default stays `BTC/USD` because it never closes.

## Your strategy lives in strategy.py

`jevloop/strategy.py` is the one file built for you to edit. It owns the
seven tunable thresholds `compose_action()` reads, plus an `apply_strategy()`
hook called on every tick with the action already chosen, free to change it
or veto it outright.

## Live trading (opt-in, off by default)

Paper is the default everywhere. Turning on live trading needs all three:

1. the `--live` flag on the command line
2. `JEV_LOOP_ALLOW_LIVE=i-understand-the-risk` in the environment
3. typing the exact confirmation phrase the CLI asks for at startup

## Dependencies

`uv`-managed virtual environment under `.venv/` with Python 3.10+ and:
- `requests>=2.31`
- `python-dotenv>=1.0`
- `matplotlib>=3.8` (optional, only for `reliability.png`)
- `pytest>=8.0` (dev only)
